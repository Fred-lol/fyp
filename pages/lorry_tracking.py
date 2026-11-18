import html
import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.alert_theme import notification_css
from components.navigation import require_staff, staff_sidebar
from components.theme import apply_theme, page_header
from services.collection_point_service import list_lorry_delivery_collection_points
from services.lorry_service import list_lorries


LKIM_KUALA_PERLIS = {
    "name": "LKIM Fisheries Complex Kuala Perlis",
    "latitude": 6.3960,
    "longitude": 100.1280,
}
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
LORRY_CRUISE_SPEED_KMH = 55
SIMULATION_DEPARTURE_DELAY_MS = 5_000
SIMULATION_SPEEDS = {
    "Real-time (1×)": 1,
    "Presentation (10×)": 10,
    "Fast demo (100×)": 100,
    "Ultra-fast demo (500×)": 500,
}


def _display_time(value):
    if not value:
        return "Not available"
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return str(value)


def _latest_location(lorry_id):
    try:
        response = requests.get(f"{API_BASE}/api/lorry/{int(lorry_id)}/location", timeout=4)
    except requests.RequestException:
        return None, "Unable to reach the tracking service. Please try again."
    if not response.ok:
        return None, "The tracking service could not retrieve this lorry location."
    return response.json(), None


def _save_location(lorry_id, latitude, longitude, accuracy_m=25):
    try:
        response = requests.post(
            f"{API_BASE}/api/location/update",
            json={"lorry_id": int(lorry_id), "latitude": float(latitude), "longitude": float(longitude), "accuracy_m": float(accuracy_m)},
            timeout=4,
        )
    except requests.RequestException:
        return False, "Unable to save the simulated lorry position."
    return (True, "") if response.ok else (False, "The tracking service rejected the simulated lorry position.")


def _distance_km(start_lat, start_lon, end_lat, end_lon):
    radius = 6371.0
    d_lat = math.radians(end_lat - start_lat)
    d_lon = math.radians(end_lon - start_lon)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(start_lat)) * math.cos(math.radians(end_lat)) * math.sin(d_lon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@st.cache_data(ttl=86_400, show_spinner=False)
def _road_route(start_lat, start_lon, end_lat, end_lon):
    """Fetch a real driving route from the public OSRM road-routing service."""
    fallback = [[start_lon, start_lat], [end_lon, end_lat]]
    try:
        response = requests.get(
            f"{OSRM_ROUTE_URL}/{start_lon},{start_lat};{end_lon},{end_lat}",
            params={"overview": "full", "geometries": "geojson"},
            timeout=10,
        )
        data = response.json() if response.ok else {}
        route = (data.get("routes") or [None])[0]
        coordinates = (route or {}).get("geometry", {}).get("coordinates") or fallback
        if len(coordinates) < 2:
            coordinates = fallback
        distance_km = float((route or {}).get("distance") or 0) / 1000
        duration_minutes = float((route or {}).get("duration") or 0) / 60
        if distance_km > 0 and duration_minutes > 0:
            return {"coordinates": coordinates, "distance_km": distance_km, "duration_minutes": duration_minutes, "source": "Road route"}
    except requests.RequestException:
        pass
    distance_km = max(_distance_km(start_lat, start_lon, end_lat, end_lon) * 1.22, 1.0)
    duration_minutes = max(20, (distance_km / 55) * 60 + 15)
    return {"coordinates": fallback, "distance_km": distance_km, "duration_minutes": duration_minutes, "source": "Estimated route"}


def _simulation_key(lorry_id):
    return f"lorry_simulation_{int(lorry_id)}"


def _lorry_travel_minutes(route):
    """Estimate travel from actual road distance at the lorry cruise speed."""
    return max(1, (float(route["distance_km"]) / LORRY_CRUISE_SPEED_KMH) * 60)


def _start_simulation(lorry_id, destination, playback_multiplier, restart=False):
    route = _road_route(LKIM_KUALA_PERLIS["latitude"], LKIM_KUALA_PERLIS["longitude"], float(destination["latitude"]), float(destination["longitude"]))
    travel_minutes = _lorry_travel_minutes(route)
    # The route is paced at a 55 km/h commercial-lorry baseline. Playback only
    # accelerates the clock for a presentation; it does not change the route.
    playback_seconds = max(1, round((travel_minutes * 60) / float(playback_multiplier)))
    ok, error = _save_location(lorry_id, LKIM_KUALA_PERLIS["latitude"], LKIM_KUALA_PERLIS["longitude"])
    if not ok:
        st.session_state.tracking_message = ("error", error)
        return
    st.session_state[_simulation_key(lorry_id)] = {
        "destination": destination,
        "route": route,
        "started_at_ms": round(time.time() * 1000),
        # Hold at the base briefly so the staff member can clearly see the
        # lorry at LKIM Kuala Perlis before even a 500x trip starts moving.
        "departure_at_ms": round(time.time() * 1000) + SIMULATION_DEPARTURE_DELAY_MS,
        "playback_ms": playback_seconds * 1000,
        "travel_minutes": travel_minutes,
        "playback_multiplier": playback_multiplier,
        "running": True,
    }
    action = "restarted" if restart else "started"
    st.session_state.tracking_message = ("success", f"Simulation {action} from LKIM Kuala Perlis using the {route['source'].lower()}.")


def _render_live_progress(simulation):
    """Update only the progress card; the rest of the page and map stay put."""
    if not simulation:
        st.metric("Simulation progress", "0%")
        return

    started_at_ms = float(simulation.get("departure_at_ms", simulation["started_at_ms"]))
    playback_ms = max(float(simulation["playback_ms"]), 1.0)

    @st.fragment(run_every="1s")
    def _progress_fragment():
        progress = min(100, max(0, round((time.time() * 1000 - started_at_ms) / playback_ms * 100)))
        st.metric("Simulation progress", f"{progress}%")

    _progress_fragment()


def _render_live_map(lorry, location, destination, simulation):
    route = simulation["route"] if simulation else _road_route(
        LKIM_KUALA_PERLIS["latitude"], LKIM_KUALA_PERLIS["longitude"], float(destination["latitude"]), float(destination["longitude"])
    )
    start_ms = int(simulation.get("departure_at_ms", simulation["started_at_ms"])) if simulation else int(time.time() * 1000)
    playback_ms = int(simulation["playback_ms"]) if simulation else 1
    position = [float(location["longitude"]), float(location["latitude"])]
    configuration = {
        "route": route["coordinates"],
        "start": [LKIM_KUALA_PERLIS["longitude"], LKIM_KUALA_PERLIS["latitude"]],
        "destination": [float(destination["longitude"]), float(destination["latitude"])],
        "initialPosition": position,
        "startedAt": start_ms,
        "playbackMs": playback_ms,
        "running": bool(simulation and simulation.get("running")),
        "apiBase": API_BASE,
        "lorryId": int(lorry["lorry_id"]),
        "lorryPlate": lorry["plate_number"],
        "destinationName": destination["point_name"],
    }
    payload = json.dumps(configuration).replace("</", "<\\/")
    components.html(
        f"""
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
        <style>
          {notification_css(st.session_state.get("theme_preference", "System"))}
          html,body,#map{{height:100%;margin:0;font-family:Inter,Segoe UI,Arial,sans-serif}}
          #map{{height:460px;border-radius:14px;overflow:hidden;border:1px solid #315363}}
          .legend{{position:absolute;z-index:1000;bottom:18px;left:14px;background:#ffffffed;color:#123b57;padding:10px 12px;border-radius:10px;font-size:13px;line-height:1.7;box-shadow:0 4px 18px #0003}}
          #progress:not(.aq-notice){{font-weight:800;color:#063b63;margin-top:7px;padding-top:7px;border-top:1px solid #cadde3}}
          .dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}} .depart{{background:#0f9d9a}} .lorry{{background:#dc3545}} .destination{{background:#f39c12}}
        </style>
        <div id="map"></div><div class="legend"><div><span class="dot depart"></span>Departure: LKIM Kuala Perlis</div><div><span class="dot lorry"></span>Current lorry position</div><div><span class="dot destination"></span>Destination</div><div id="progress">Simulation progress: 0%</div></div>
        <script>
          const config = {payload};
          const map = L.map('map', {{zoomControl:true}});
          L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom:19, attribution:'© OpenStreetMap contributors'}}).addTo(map);
          const routeLatLngs = config.route.map(p => [p[1], p[0]]);
          const routeLine = L.polyline(routeLatLngs, {{color:'#48b1be',weight:5,opacity:.85}}).addTo(map);
          const departure = L.circleMarker([config.start[1],config.start[0]], {{radius:9,color:'#087f7b',fillColor:'#0f9d9a',fillOpacity:1,weight:2}}).addTo(map).bindTooltip('Departure: LKIM Kuala Perlis');
          const destination = L.circleMarker([config.destination[1],config.destination[0]], {{radius:9,color:'#b66b00',fillColor:'#f39c12',fillOpacity:1,weight:2}}).addTo(map).bindTooltip('Destination: ' + config.destinationName);
          const lorry = L.circleMarker([config.initialPosition[1],config.initialPosition[0]], {{radius:11,color:'#8b1d29',fillColor:'#dc3545',fillOpacity:1,weight:3}}).addTo(map).bindTooltip('Lorry ' + config.lorryPlate, {{permanent:true,direction:'top'}});
          map.fitBounds(routeLine.getBounds(), {{padding:[38,38]}});
          function segmentDistance(a,b) {{ const dx=b[0]-a[0], dy=b[1]-a[1]; return Math.sqrt(dx*dx+dy*dy); }}
          const lengths=[]; let total=0; for(let i=1;i<config.route.length;i++){{const length=segmentDistance(config.route[i-1],config.route[i]); lengths.push(length); total+=length;}}
          function routePosition(progress) {{
            if (!config.route.length) return config.initialPosition;
            let remaining=Math.min(1,Math.max(0,progress))*total;
            for(let i=1;i<config.route.length;i++){{const length=lengths[i-1]; if(remaining<=length || i===config.route.length-1){{const t=length ? remaining/length : 0; const a=config.route[i-1],b=config.route[i]; return [a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t];}} remaining-=length;}}
            return config.route[config.route.length-1];
          }}
          let lastSaved=0, arrivalSent=false;
          const progressLabel=document.getElementById('progress');
          function showArrival(kind, text) {{
            progressLabel.className = 'aq-notice';
            progressLabel.dataset.kind = kind;
            progressLabel.textContent = text;
          }}
          function finishTrip() {{
            if(arrivalSent) return; arrivalSent=true;
            fetch(config.apiBase+'/api/lorry/'+config.lorryId+'/arrive',{{method:'POST'}})
              .then(response=>response.json())
              .then(data=>showArrival(data.success ? 'success' : 'error', data.success ? 'Arrived — lorry is now Available' : 'Arrived — status update failed'))
              .catch(()=>showArrival('error', 'Arrived — unable to update lorry status'));
          }}
          function animate() {{
            if(config.running){{
              const progress=Math.min(1,(Date.now()-config.startedAt)/config.playbackMs);
              const point=routePosition(progress); lorry.setLatLng([point[1],point[0]]);
              progressLabel.textContent='Simulation progress: '+Math.round(progress*100)+'%';
              if(Date.now()-lastSaved>15000 || progress>=1){{ lastSaved=Date.now(); fetch(config.apiBase+'/api/location/update',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{lorry_id:config.lorryId,latitude:point[1],longitude:point[0],accuracy_m:25}})}}).catch(()=>{{}}); }}
              if(progress<1) requestAnimationFrame(animate); else finishTrip();
            }}
          }}
          animate();
        </script>
        """,
        height=470,
        scrolling=False,
    )


bootstrap_app()
st.set_page_config(page_title="Lorry Tracking | AquaLoad", page_icon="L", layout="wide")
apply_theme(); staff_sidebar(); require_staff()
page_header("Lorry Tracking", "Monitor active lorries and simulate a smooth West Malaysia road journey from AquaLoad's LKIM Kuala Perlis base.", "Live Tracking")

API_BASE = os.getenv("AQUALOAD_TRACKING_API", "http://127.0.0.1:8000")
try:
    api_online = requests.get(f"{API_BASE}/api/health", timeout=3).ok
except requests.RequestException:
    api_online = False
if not api_online:
    st.error("Live tracking is unavailable. Check that the AquaLoad Tracking API is running, then try again.")
    st.stop()

active_lorries = list_lorries("In Transit")
if not active_lorries:
    st.info("No lorry is currently in transit. A lorry appears here after an approved loading plan marks its orders as Loaded.")
    st.stop()
lorry_by_id = {int(lorry["lorry_id"]): lorry for lorry in active_lorries}
selected_lorry_id = st.selectbox("Active lorry", list(lorry_by_id), format_func=lambda lorry_id: f"{lorry_by_id[lorry_id]['plate_number']} — In Transit")
selected_lorry = lorry_by_id[selected_lorry_id]

points = list_lorry_delivery_collection_points("Available")
if not points:
    st.error("No destination collection point is available for simulation.")
    st.stop()
point_map = {f"{point['point_name']} · {point['city']}, {point['state']}": point for point in points}
# Keep speed and destination changes in the browser until staff deliberately
# starts or restarts the trip. This avoids a page rerun for every selection.
with st.form("simulation_controls", border=False):
    destination_label = st.selectbox(
        "Simulation destination", list(point_map), key=f"simulation_destination_{selected_lorry_id}"
    )
    selected_speed_label = st.selectbox("Simulation speed", list(SIMULATION_SPEEDS), index=1)
    destination = point_map[destination_label]
    selected_speed = SIMULATION_SPEEDS[selected_speed_label]
    preview_route = _road_route(
        LKIM_KUALA_PERLIS["latitude"], LKIM_KUALA_PERLIS["longitude"],
        float(destination["latitude"]), float(destination["longitude"]),
    )
    lorry_minutes = _lorry_travel_minutes(preview_route)
    sim_a, sim_b, sim_c = st.columns(3)
    sim_a.metric("Departure", "LKIM Kuala Perlis")
    sim_b.metric("Road Distance", f"{preview_route['distance_km']:,.0f} km")
    sim_c.metric("Lorry Travel Time", f"{int(lorry_minutes) // 60}h {int(lorry_minutes) % 60}m")
    start_col, restart_col = st.columns(2)
    with start_col:
        start_clicked = st.form_submit_button(
            "Start simulation", icon=":material/play_arrow:", type="primary", use_container_width=True
        )
    with restart_col:
        restart_clicked = st.form_submit_button(
            "Restart simulation", icon=":material/restart_alt:", type="primary", use_container_width=True
        )

if start_clicked:
    _start_simulation(selected_lorry_id, destination, selected_speed)
    st.rerun()
if restart_clicked:
    _start_simulation(selected_lorry_id, destination, selected_speed, restart=True)
    st.rerun()
if message := st.session_state.pop("tracking_message", None):
    getattr(st, message[0])(message[1])

location, error = _latest_location(selected_lorry_id)
if error:
    st.error(error)
    st.stop()
if not location.get("available"):
    st.warning(f"No location has been recorded for {selected_lorry['plate_number']} yet. Start the simulation to place it at LKIM Kuala Perlis.")
    st.stop()

simulation = st.session_state.get(_simulation_key(selected_lorry_id))
# A simulation can be reset outside this page (for example, before a demo).
# When its lorry is recorded back at the LKIM departure point, discard any
# completed browser timer so the map, marker and progress all return to 0%.
if simulation:
    at_departure = (
        abs(float(location.get("latitude") or 0) - LKIM_KUALA_PERLIS["latitude"]) < 0.0001
        and abs(float(location.get("longitude") or 0) - LKIM_KUALA_PERLIS["longitude"]) < 0.0001
    )
    departure_at_ms = float(simulation.get("departure_at_ms", simulation["started_at_ms"]))
    completed = (time.time() * 1000 - departure_at_ms) >= float(simulation["playback_ms"])
    if at_departure and completed:
        st.session_state.pop(_simulation_key(selected_lorry_id), None)
        st.rerun()

st.subheader(f"{selected_lorry['plate_number']} live position", anchor=False)
map_a, map_b, map_c = st.columns(3)
map_a.metric("Lorry status", "In Transit")
map_b.metric("Last saved update", _display_time(location.get("recorded_at")))
with map_c:
    _render_live_progress(simulation)
_render_live_map(selected_lorry, location, simulation["destination"] if simulation else destination, simulation)
