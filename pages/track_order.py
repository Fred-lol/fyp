import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.cards import empty_state
from components.navigation import customer_sidebar
from components.theme import apply_theme, page_header
from components.tables import render_dataframe
from services.order_service import get_order, list_customer_orders
from services.tracking_service import get_order_tracking
from services.payment_service import payment_status_label


LKIM_KUALA_PERLIS = (6.3960, 100.1280)
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving"
TRACKING_API_BASE = os.getenv("AQUALOAD_TRACKING_API", "http://127.0.0.1:8000")


def _display_timestamp(value):
    if not value:
        return "Not available"
    if isinstance(value, datetime):
        return value.strftime("%d %b %Y, %I:%M %p")
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).strftime("%d %b %Y, %I:%M %p")
    except ValueError:
        return str(value)


def _next_step(status):
    steps = {
        "Pending": "Your order is paid and waiting for staff confirmation.",
        "Confirmed": "Staff are preparing your order for loading.",
        "Ready for Pickup": "Your order is ready for collection at LKIM Fisheries Complex Kuala Perlis. Please bring your order reference when collecting it.",
        "Ready for Loading": "Your seafood is ready and will be assigned to a lorry shortly.",
        "Loaded": "Your seafood is on the lorry. Its current position is shown below.",
        "Completed": "This order has been completed. Please collect it from the assigned collection point.",
        "Cancelled": "This order was cancelled. No further delivery action is required.",
    }
    return steps.get(status, "Staff will update this order as it moves through fulfilment.")


def _distance_km(start_lat, start_lon, end_lat, end_lon):
    radius = 6371.0
    d_lat = math.radians(end_lat - start_lat)
    d_lon = math.radians(end_lon - start_lon)
    a = math.sin(d_lat / 2) ** 2 + math.cos(math.radians(start_lat)) * math.cos(math.radians(end_lat)) * math.sin(d_lon / 2) ** 2
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@st.cache_data(ttl=86_400, show_spinner=False)
def _road_route(destination_lat, destination_lon):
    fallback = [[LKIM_KUALA_PERLIS[1], LKIM_KUALA_PERLIS[0]], [destination_lon, destination_lat]]
    try:
        response = requests.get(
            f"{OSRM_ROUTE_URL}/{LKIM_KUALA_PERLIS[1]},{LKIM_KUALA_PERLIS[0]};{destination_lon},{destination_lat}",
            params={"overview": "full", "geometries": "geojson"}, timeout=10,
        )
        route = (response.json().get("routes") or [None])[0] if response.ok else None
        coordinates = (route or {}).get("geometry", {}).get("coordinates") or fallback
        if len(coordinates) >= 2:
            return coordinates
    except requests.RequestException:
        pass
    return fallback


def _render_customer_map(data):
    latest = data["latest_location"]
    destination_lat = float(data["destination_latitude"])
    destination_lon = float(data["destination_longitude"])
    configuration = {
        "route": _road_route(destination_lat, destination_lon),
        "start": [LKIM_KUALA_PERLIS[1], LKIM_KUALA_PERLIS[0]],
        "destination": [destination_lon, destination_lat],
        "initial": [float(latest["longitude"]), float(latest["latitude"])],
        "lorryPlate": data.get("plate_number") or "Assigned lorry",
        "destinationName": data.get("collection_point") or "Collection point",
        "trackingUrl": f"{TRACKING_API_BASE}/api/orders/{int(data['order_id'])}/tracking?customer_id={int(data['customer_id'])}",
    }
    payload = json.dumps(configuration).replace("</", "<\\/")
    components.html(
        f"""
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" crossorigin="" />
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" crossorigin=""></script>
        <style>
          html,body,#map{{height:100%;margin:0;font-family:Inter,Segoe UI,Arial,sans-serif}} #map{{height:460px;border-radius:14px;overflow:hidden;border:1px solid #315363}}
          .legend{{position:absolute;z-index:1000;bottom:18px;left:14px;background:#ffffffed;color:#123b57;padding:10px 12px;border-radius:10px;font-size:13px;line-height:1.7;box-shadow:0 4px 18px #0003}}
          .dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:6px}} .depart{{background:#0f9d9a}} .lorry{{background:#dc3545}} .destination{{background:#f39c12}}
        </style>
        <div id="map"></div><div class="legend"><div><span class="dot depart"></span>Departure: LKIM Kuala Perlis</div><div><span class="dot lorry"></span>Current lorry position</div><div><span class="dot destination"></span>Destination</div></div>
        <script>
          const config={payload}; const map=L.map('map',{{zoomControl:true}});
          L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{maxZoom:19,attribution:'© OpenStreetMap contributors'}}).addTo(map);
          const route=L.polyline(config.route.map(p=>[p[1],p[0]]),{{color:'#48b1be',weight:5,opacity:.85}}).addTo(map);
          L.circleMarker([config.start[1],config.start[0]],{{radius:9,color:'#087f7b',fillColor:'#0f9d9a',fillOpacity:1,weight:2}}).addTo(map).bindTooltip('Departure: LKIM Kuala Perlis');
          L.circleMarker([config.destination[1],config.destination[0]],{{radius:9,color:'#b66b00',fillColor:'#f39c12',fillOpacity:1,weight:2}}).addTo(map).bindTooltip('Destination: '+config.destinationName);
          const lorry=L.circleMarker([config.initial[1],config.initial[0]],{{radius:11,color:'#8b1d29',fillColor:'#dc3545',fillOpacity:1,weight:3}}).addTo(map).bindTooltip('Lorry '+config.lorryPlate,{{permanent:true,direction:'top'}});
          map.fitBounds(route.getBounds(),{{padding:[38,38]}}); let current=config.initial;
          function moveTo(target){{const from=current,started=Date.now(),duration=12000; function frame(){{const t=Math.min(1,(Date.now()-started)/duration); const lon=from[0]+(target[0]-from[0])*t,lat=from[1]+(target[1]-from[1])*t; lorry.setLatLng([lat,lon]); if(t<1)requestAnimationFrame(frame); else current=target;}} requestAnimationFrame(frame);}}
          async function poll(){{try{{const response=await fetch(config.trackingUrl); const data=await response.json(); if(data.latest_location)moveTo([Number(data.latest_location.longitude),Number(data.latest_location.latitude)]);}}catch(error){{}} setTimeout(poll,15000);}} poll();
        </script>
        """, height=470, scrolling=False,
    )


bootstrap_app()
st.set_page_config(page_title="Track Order | AquaLoad", page_icon="T", layout="wide")
apply_theme(); customer_sidebar()
page_header("Track Order", "View your order status, assigned collection point and the latest location of the lorry carrying your order.", "Order Tracking")

orders = [
    order for order in list_customer_orders(st.session_state.user_id)
    if order.get("status") != "Cancelled"
]
if not orders:
    # Cancelled orders remain visible in My Orders as a record, but they have
    # no collection or lorry journey to track.
    st.session_state.pop("selected_order_id", None)
    empty_state("You do not have any active orders to track.")
    st.stop()
ids = [order["order_id"] for order in orders]
default_id = st.session_state.get("selected_order_id") if st.session_state.get("selected_order_id") in ids else ids[0]
selected = st.selectbox("Select Order", ids, index=ids.index(default_id), format_func=lambda order_id: f"Order #{order_id}")
st.session_state.selected_order_id = selected
order = get_order(selected, st.session_state.user_id)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Order", f"#{order['order_id']}")
c2.metric("Current Status", order["status"])
c3.metric("Payment", payment_status_label((order.get("payment") or {}).get("payment_status")))
c4.metric("Order Total", f"RM {float(order.get('total_amount') or 0):,.2f}")
st.info(_next_step(order["status"]))

left, right = st.columns(2, gap="large")
with left:
    st.markdown("### Collection Point")
    collection_name = order.get("collection_point_name") or order.get("collection_point") or "Not assigned yet"
    st.markdown(f"**{collection_name}**")
    if order.get("collection_point_address"):
        st.write(order["collection_point_address"])
    location = ", ".join(part for part in [order.get("collection_point_city"), order.get("collection_point_state")] if part)
    if location:
        st.write(location)
    if order.get("collection_assignment") == "Local Pickup":
        st.info(f"Self-pickup: collect this order from {collection_name}. No lorry delivery is required.")
    if collection_name == "Not assigned yet":
        st.info("Staff will assign a collection point before loading is arranged.")
with right:
    st.markdown("### Order Summary")
    st.metric("Total Seafood Weight", f"{order['total_weight_kg']:g} kg")
    st.caption(f"Last updated: {_display_timestamp(order.get('updated_at'))}")
    item_rows = [{"Seafood": item["product_name"], "Quantity": f"{float(item['quantity']):g} {item['unit']}"} for item in order["items"]]
    render_dataframe(pd.DataFrame(item_rows), use_container_width=True, hide_index=True)

if order.get("collection_assignment") == "Local Pickup":
    st.stop()

st.divider()
st.markdown("## Live Lorry Location")
ok, data = get_order_tracking(order["order_id"], st.session_state.user_id)
if not ok:
    st.warning(data)
    st.stop()
if not data.get("lorry_id"):
    st.info(data.get("assignment_message") or "A lorry has not been assigned yet. Live tracking becomes available when the order is loaded.")
    st.stop()

a, b, c = st.columns(3)
a.metric("Assigned Lorry", data.get("plate_number") or "Not assigned")
b.metric("Destination", data.get("collection_point") or "Not assigned")
latest = data.get("latest_location")
c.metric("Last saved update", _display_timestamp((latest or {}).get("recorded_at")))
if not data.get("location_available") or not latest:
    st.info("The lorry location is not available yet.")
    st.stop()
if data.get("destination_latitude") is None or data.get("destination_longitude") is None:
    st.warning("The destination location is not configured yet.")
    st.stop()
_render_customer_map(data)
