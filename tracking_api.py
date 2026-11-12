"""AquaLoad REST API for lorry location tracking.

Run in a second terminal:
    python -m uvicorn tracking_api:app --reload --port 8000

Driver/Staff test page:
    http://127.0.0.1:8000/driver

FastAPI docs:
    http://127.0.0.1:8000/docs
"""

from pathlib import Path
import sys

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from database.db import db_session
from database.schema import initialize_schema

# The API service must prepare its database schema, but it must not call the
# Streamlit bootstrap because that bootstrap manages the API process itself.
initialize_schema()

app = FastAPI(title="AquaLoad Tracking REST API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class LocationUpdate(BaseModel):
    lorry_id: int
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    accuracy_m: float | None = Field(default=None, ge=0)


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AquaLoad Tracking REST API"}


@app.get("/api/lorries")
def lorries():
    with db_session() as conn:
        rows = conn.execute(
            "SELECT lorry_id,plate_number,status FROM lorry_profiles WHERE status='In Transit' ORDER BY plate_number"
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/location/update")
def update_location(payload: LocationUpdate):
    with db_session() as conn:
        lorry = conn.execute(
            "SELECT lorry_id,plate_number FROM lorry_profiles WHERE lorry_id=?",
            (payload.lorry_id,),
        ).fetchone()
        if not lorry:
            raise HTTPException(status_code=404, detail="Lorry not found.")
        conn.execute(
            """
            INSERT INTO lorry_locations(lorry_id,latitude,longitude,accuracy_m)
            VALUES(?,?,?,?)
            """,
            (payload.lorry_id, payload.latitude, payload.longitude, payload.accuracy_m),
        )
    return {
        "success": True,
        "lorry_id": payload.lorry_id,
        "message": "Latest lorry location saved.",
    }


@app.post("/api/lorry/{lorry_id}/arrive")
def mark_lorry_arrived(lorry_id: int):
    """Complete a simulated trip and release the lorry for its next journey."""
    with db_session() as conn:
        lorry = conn.execute(
            "SELECT lorry_id,plate_number,status FROM lorry_profiles WHERE lorry_id=?",
            (lorry_id,),
        ).fetchone()
        if not lorry:
            raise HTTPException(status_code=404, detail="Lorry not found.")
        if lorry["status"] == "In Transit":
            conn.execute(
                "UPDATE lorry_profiles SET status='Available',updated_at=CURRENT_TIMESTAMP WHERE lorry_id=?",
                (lorry_id,),
            )
    return {
        "success": True,
        "lorry_id": lorry_id,
        "plate_number": lorry["plate_number"],
        "status": "Available",
        "message": f"{lorry['plate_number']} arrived and is now Available for its next trip.",
    }


@app.get("/api/lorry/{lorry_id}/location")
def latest_lorry_location(lorry_id: int):
    with db_session() as conn:
        row = conn.execute(
            """
            SELECT ll.*,l.plate_number
            FROM lorry_locations ll
            JOIN lorry_profiles l ON l.lorry_id=ll.lorry_id
            WHERE ll.lorry_id=?
            ORDER BY ll.recorded_at DESC,ll.location_id DESC
            LIMIT 1
            """,
            (lorry_id,),
        ).fetchone()
    if not row:
        return {"available": False, "lorry_id": lorry_id}
    result = dict(row)
    result["available"] = True
    return result


@app.get("/api/orders/{order_id}/tracking")
def order_tracking(order_id: int, customer_id: int = Query(..., ge=1)):
    """Return tracking only when the order belongs to the supplied Customer."""
    with db_session() as conn:
        order = conn.execute(
            """
            SELECT o.order_id,o.customer_id,o.status,o.collection_point_id,o.collection_point,
                   cp.latitude destination_latitude,cp.longitude destination_longitude,
                   cp.city destination_city,cp.state destination_state,
                   p.plan_id,p.lorry_id,l.plate_number
            FROM seafood_orders o
            LEFT JOIN collection_points cp ON cp.collection_point_id=o.collection_point_id
            LEFT JOIN loading_plan_orders po ON po.order_id=o.order_id
            LEFT JOIN loading_plans p ON p.plan_id=po.plan_id
            LEFT JOIN lorry_profiles l ON l.lorry_id=p.lorry_id
            WHERE o.order_id=? AND o.customer_id=?
            ORDER BY p.created_at DESC
            LIMIT 1
            """,
            (order_id, customer_id),
        ).fetchone()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found for this Customer.")

        latest = None
        if order["lorry_id"]:
            latest = conn.execute(
                """
                SELECT latitude,longitude,accuracy_m,recorded_at
                FROM lorry_locations
                WHERE lorry_id=?
                ORDER BY recorded_at DESC,location_id DESC
                LIMIT 1
                """,
                (order["lorry_id"],),
            ).fetchone()

    response = dict(order)
    response["location_available"] = latest is not None
    response["latest_location"] = dict(latest) if latest else None
    return response


DRIVER_HTML = r"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AquaLoad Lorry Location Sharing</title>
<style>
:root{font-family:Inter,Segoe UI,Arial,sans-serif;color:#173b58;background:#eef7f8}
body{margin:0;padding:24px}.card{max-width:580px;margin:auto;background:#fff;border:1px solid #dceaf0;border-radius:22px;padding:24px;box-shadow:0 16px 42px rgba(9,54,75,.08)}
h1{color:#062e55;margin:0 0 8px}.muted{color:#647d90;line-height:1.6}select,button{width:100%;min-height:48px;border-radius:11px;border:1px solid #dceaf0;padding:0 12px;font-size:15px;margin-top:10px}button{background:linear-gradient(135deg,#087ead,#0db4b9);color:#fff;font-weight:800;border:none;cursor:pointer}.stop{background:#fff;color:#a74d3c;border:1px solid #f0c9bf}.status{margin-top:18px;padding:14px;border-radius:12px;background:#f7fbfd;line-height:1.65}.ok{color:#087d74;font-weight:800}.warn{color:#8c6514;font-weight:800}
</style>
</head>
<body>
<div class="card">
  <div style="font-size:11px;font-weight:800;letter-spacing:1.5px;color:#009c9a">AQUALOAD STAFF TRACKING</div>
  <h1>Share Lorry Location</h1>
  <p class="muted">Use the assigned lorry driver's device to share its latest GPS position with the AquaLoad REST API.</p>
  <label>Assigned Lorry</label>
  <select id="lorry"></select>
  <button id="start">Start Sharing Location</button>
  <button id="stop" class="stop">Stop Sharing</button>
  <div class="status" id="status"><span class="warn">Location sharing is not active.</span></div>
  <p class="muted" style="font-size:12px">Browser GPS normally requires HTTPS when this page is opened from another phone/device. Localhost is allowed for development.</p>
</div>
<script>
let watchId=null; let lastSent=0;
const statusEl=document.getElementById('status');
async function loadLorries(){
  const rows=await fetch('/api/lorries').then(r=>r.json());
  document.getElementById('lorry').innerHTML=rows.map(x=>`<option value="${x.lorry_id}">${x.plate_number}</option>`).join('');
}
async function sendPosition(pos){
  const now=Date.now(); if(now-lastSent<25000) return; lastSent=now;
  const lorryId=Number(document.getElementById('lorry').value);
  const payload={lorry_id:lorryId,latitude:pos.coords.latitude,longitude:pos.coords.longitude,accuracy_m:pos.coords.accuracy};
  const response=await fetch('/api/location/update',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(response.ok){statusEl.innerHTML=`<span class="ok">Sharing location</span><br>Latitude: ${payload.latitude.toFixed(6)}<br>Longitude: ${payload.longitude.toFixed(6)}<br>Accuracy: ${Math.round(payload.accuracy_m||0)} m<br>Updated: ${new Date().toLocaleTimeString()}`}
  else{statusEl.innerHTML='<span class="warn">Unable to send location to AquaLoad.</span>'}
}
document.getElementById('start').onclick=()=>{
  if(!navigator.geolocation){statusEl.innerHTML='<span class="warn">Geolocation is not supported by this browser.</span>';return;}
  if(watchId!==null) navigator.geolocation.clearWatch(watchId);
  watchId=navigator.geolocation.watchPosition(sendPosition,e=>{statusEl.innerHTML=`<span class="warn">GPS error:</span> ${e.message}`},{enableHighAccuracy:true,maximumAge:10000,timeout:15000});
};
document.getElementById('stop').onclick=()=>{if(watchId!==null){navigator.geolocation.clearWatch(watchId);watchId=null;}statusEl.innerHTML='<span class="warn">Location sharing stopped.</span>';};
loadLorries();
</script>
</body>
</html>
"""


@app.get("/driver", response_class=HTMLResponse)
def driver_page():
    return DRIVER_HTML
