import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from bootstrap import bootstrap_app
from components.theme import apply_theme, page_header
from components.navigation import staff_sidebar, require_staff
from components.alert_theme import notification_css
from components.feedback import flash
from services.optimization_service import list_plans, get_plan, save_optimization, saved_weight_utilization


def _preview_as_plan(result):
    """Adapt an unsaved optimizer response to the 3D viewer's plan shape."""
    lorry = result["lorry"]
    metrics = result["metrics"]
    return {
        "plan_id": None,
        "plate_number": lorry["plate_number"],
        "internal_length": lorry["internal_length"],
        "internal_width": lorry["internal_width"],
        "internal_height": lorry["internal_height"],
        "validation_result": "Valid",
        "orders": [{"order_id": order_id} for order_id in result["order_ids"]],
        "placements": result["placements"],
        "space_utilization": metrics["space_utilization"],
        "total_weight": metrics["total_weight"],
        "remaining_weight_capacity": metrics["remaining_weight_capacity"],
        "collection_point": result.get("collection_point"),
    }

bootstrap_app()
st.set_page_config(page_title="3D Loading Plan | AquaLoad", page_icon="🧊", layout="wide")
apply_theme(); staff_sidebar(keep_loading_preview=True); require_staff()
page_header(
    "3D Loading Visualization",
    "Inspect the exact saved box coordinates inside the selected lorry and follow the physical loading sequence.",
    "Loading Guide",
)

preview_result = st.session_state.get("loading_plan_preview")
is_preview = bool(preview_result and preview_result.get("success"))
plans = ([{"plan_id": -1, "plate_number": "3D Preview", "collection_point": "Not saved yet"}]
         if is_preview else list_plans())
if not plans:
    st.info("No saved loading plan is available yet. Generate and save a valid plan first.")
    st.stop()

plan_ids = [p["plan_id"] for p in plans]
default_plan = st.session_state.get("selected_plan_id")
if default_plan not in plan_ids:
    default_plan = plan_ids[0]

plan_id = st.selectbox(
    "3D Preview" if is_preview else "Saved Loading Plan",
    plan_ids,
    index=plan_ids.index(default_plan),
    format_func=lambda pid: next(
        f"Plan #{p['plan_id']} · {p['plate_number']} · {p.get('collection_point') or 'No collection point'}"
        for p in plans if p["plan_id"] == pid
    ),
)
st.session_state.selected_plan_id = plan_id
plan = _preview_as_plan(preview_result) if is_preview else get_plan(plan_id)

if not plan:
    st.info("This loading plan is no longer in the current 30-day view.")
    st.stop()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Plan", "3D Preview" if is_preview else f"#{plan['plan_id']}")
c2.metric("Lorry", plan["plate_number"])
c3.metric("Orders", len(plan["orders"]))
c4.metric("Boxes", len(plan["placements"]))
c5.metric("Validation", "✓ Valid" if plan["validation_result"] == "Valid" else plan["validation_result"])
st.caption(f"Destination: {plan.get('collection_point') or 'Not assigned'}")

scene_data = {
    "lorry": {
        "length": float(plan["internal_length"]),
        "width": float(plan["internal_width"]),
        "height": float(plan["internal_height"]),
        "plate": plan["plate_number"],
    },
    "boxes": [{
        "placement_id": int(p.get("placement_id") or 0),
        "order_id": int(p["order_id"]),
        "customer_name": p.get("customer_name", "Customer"),
        "box_label": p.get("box_label") or f"O{int(p['order_id'])}-B{int(p.get('box_instance') or 1):02d}",
        "box_profile_id": int(p["box_profile_id"]),
        "box_name": p["box_name"],
        "capacity_litre": int(p.get("capacity_litre") or 0),
        "sequence": int(p["sequence_number"]),
        "x": float(p["x"]),
        "y": float(p["y"]),
        "z": float(p["z"]),
        "l": float(p["placed_length"]),
        "w": float(p["placed_width"]),
        "h": float(p["placed_height"]),
        "weight": float(p["loaded_weight"]),
        "orientation": p["orientation"],
    } for p in plan["placements"]],
}
data_json = json.dumps(scene_data)

three_html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
{notification_css(st.session_state.get("theme_preference", "System"))}
html,body,#viewer{{margin:0;width:100%;height:100%;overflow:hidden;font-family:Inter,Segoe UI,Arial,sans-serif}}
#viewer{{position:relative;background:#071f32}}
.panel{{position:absolute;z-index:5;background:rgba(3,28,53,.90);color:#eefbfc;border:1px solid rgba(255,255,255,.10);border-radius:12px;padding:12px 14px;font-size:12px;line-height:1.55;backdrop-filter:blur(8px)}}
#help{{left:16px;top:16px}}#legend{{right:16px;top:16px;max-width:280px}}#selected{{left:16px;bottom:16px;min-width:260px;max-width:360px}}
#views{{position:absolute;z-index:6;left:50%;top:16px;transform:translateX(-50%);display:flex;gap:6px;flex-wrap:wrap;justify-content:center}}
#sequence{{position:absolute;z-index:6;right:16px;bottom:16px;display:flex;align-items:center;gap:6px;background:rgba(3,28,53,.90);padding:8px;border-radius:12px;border:1px solid rgba(255,255,255,.10)}}
button{{border:1px solid rgba(255,255,255,.16);background:#fff;color:#073c5c;border-radius:8px;padding:8px 10px;font-weight:700;cursor:pointer}}button:hover{{background:#eaf8f8}}
#stepLabel{{color:#fff;min-width:76px;text-align:center;font-size:12px;font-weight:700}}
.dot{{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:7px;vertical-align:middle}}.muted{{color:#a9c2cf}}
.world-label{{padding:5px 8px;border-radius:7px;font-size:11px;font-weight:800;letter-spacing:.04em;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.35)}}
.world-label.gate{{background:rgba(255,162,77,.95);color:#311605}}.world-label.deep{{background:rgba(103,230,225,.95);color:#032633}}
canvas{{display:block}}
@media(max-width:760px){{#legend{{display:none}}#views{{top:65px}}#selected{{max-width:260px}}}}
</style>
<script type="importmap">
{{
  "imports": {{
    "three": "https://cdn.jsdelivr.net/npm/three@0.167.1/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.167.1/examples/jsm/"
  }}
}}
</script>
</head>
<body>
<div id="viewer">
  <div id="help" class="panel"><strong>AquaLoad 3D Loading Plan</strong><br>Drag to rotate · Scroll to zoom · Right-drag to pan<br><span class="muted">Boxes remain horizontal. Load deepest-to-gate, floor layer before upper layers.</span></div>
  <div id="legend" class="panel"></div>
  <div id="selected" class="panel">Click a box to view its Order, size, weight and loading sequence.</div>
  <div id="views">
    <button id="view3d">3D View</button><button id="front">Front</button><button id="side">Side</button><button id="top">Top</button><button id="reset">Reset</button>
  </div>
  <div id="sequence">
    <button id="prev">◀</button><button id="play">▶ Play</button><button id="pause">Pause</button><button id="restart">↺</button><button id="all">Show All</button><button id="next">▶</button><span id="stepLabel"></span>
  </div>
</div>
<script type="module">
const data = {data_json};
const viewer = document.getElementById('viewer');
const selectedPanel = document.getElementById('selected');
const legendPanel = document.getElementById('legend');

async function start() {{
try {{
  const THREE = await import('three');
  const {{ OrbitControls }} = await import('three/addons/controls/OrbitControls.js');
  const {{ CSS2DRenderer, CSS2DObject }} = await import('three/addons/renderers/CSS2DRenderer.js');
  const scene = new THREE.Scene();
  const systemDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  scene.background = new THREE.Color(systemDark ? 0x071a27 : 0x071f32);

  const L=data.lorry.length, W=data.lorry.width, H=data.lorry.height;
  const maxDim=Math.max(L,W,H);
  const camera=new THREE.PerspectiveCamera(44,viewer.clientWidth/viewer.clientHeight,0.1,maxDim*20);
  const renderer=new THREE.WebGLRenderer({{antialias:true}});
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
  renderer.setSize(viewer.clientWidth,viewer.clientHeight);
  viewer.appendChild(renderer.domElement);
  const labelRenderer=new CSS2DRenderer();
  labelRenderer.setSize(viewer.clientWidth,viewer.clientHeight);
  labelRenderer.domElement.style.position='absolute';labelRenderer.domElement.style.top='0';labelRenderer.domElement.style.left='0';labelRenderer.domElement.style.pointerEvents='none';
  viewer.appendChild(labelRenderer.domElement);

  const controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=true; controls.dampingFactor=.08; controls.screenSpacePanning=true;
  const center=new THREE.Vector3(L/2,H/2,W/2);
  function normalUp(){{camera.up.set(0,1,0);}}
  function set3D(){{normalUp();camera.position.set(L*1.25,H*1.25,W*2.2);controls.target.copy(center);controls.update();}}
  // Front = looking in through the rear loading gate. Side = the long
  // gate-to-deepest-end profile of the lorry.
  function frontView(){{normalUp();camera.position.set(-maxDim*2.2,H/2,W/2);controls.target.copy(center);controls.update();}}
  function sideView(){{normalUp();camera.position.set(L/2,H/2,W/2+maxDim*2.2);controls.target.copy(center);controls.update();}}
  function topView(){{camera.up.set(0,0,-1);camera.position.set(L/2,H/2+maxDim*2.2,W/2);controls.target.set(L/2,0,W/2);controls.update();}}
  set3D();

  scene.add(new THREE.HemisphereLight(0xffffff,0x21485b,2.1));
  const dir=new THREE.DirectionalLight(0xffffff,2.2);dir.position.set(L,H*2,W*2);scene.add(dir);

  // Lorry wireframe and semi-transparent floor.
  const lorryGeo=new THREE.BoxGeometry(L,H,W);
  const wire=new THREE.LineSegments(new THREE.EdgesGeometry(lorryGeo),new THREE.LineBasicMaterial({{color:0x67e6e1}}));
  wire.position.copy(center);scene.add(wire);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(L,W),new THREE.MeshBasicMaterial({{color:0x16495c,transparent:true,opacity:.38,side:THREE.DoubleSide}}));
  floor.rotation.x=-Math.PI/2;floor.position.set(L/2,.05,W/2);scene.add(floor);

  // The rear gate is at X=0. Showing it in the scene makes the physical
  // deep-end-first loading sequence clear to the loading crew.
  const gate=new THREE.Mesh(
    new THREE.PlaneGeometry(W,H),
    new THREE.MeshBasicMaterial({{color:0xffa24d,transparent:true,opacity:.20,side:THREE.DoubleSide}})
  );
  gate.rotation.y=Math.PI/2;gate.position.set(.5,H/2,W/2);scene.add(gate);
  const gateEdges=new THREE.LineSegments(
    new THREE.EdgesGeometry(new THREE.PlaneGeometry(W,H)),
    new THREE.LineBasicMaterial({{color:0xffbe75,transparent:true,opacity:.95}})
  );
  gateEdges.rotation.y=Math.PI/2;gateEdges.position.set(.5,H/2,W/2);scene.add(gateEdges);
  const deepWall=new THREE.Mesh(
    new THREE.PlaneGeometry(W,H),
    new THREE.MeshBasicMaterial({{color:0x31d8d0,transparent:true,opacity:.10,side:THREE.DoubleSide}})
  );
  deepWall.rotation.y=Math.PI/2;deepWall.position.set(L-.5,H/2,W/2);scene.add(deepWall);
  function addEndLabel(text, className, position){{
    const element=document.createElement('div');element.className='world-label '+className;element.textContent=text;
    const label=new CSS2DObject(element);label.position.copy(position);scene.add(label);
  }}
  addEndLabel('REAR LOADING GATE','gate',new THREE.Vector3(0,H+18,W/2));
  addEndLabel('DEEPEST END','deep',new THREE.Vector3(L,H+18,W/2));

  const palette=[0x12b8b0,0x2f91d1,0xe69454,0x9b7bd8,0xe16c73,0x5ac07d,0xd6af43,0x5c9aa5];
  const boxTypes=[...new Map(data.boxes.map(b=>[b.box_profile_id,b])).values()];
  const boxColor=new Map(boxTypes.map((box,i)=>[box.box_profile_id,palette[i%palette.length]]));
  legendPanel.innerHTML='<strong>Box Size Colours</strong><br>'+boxTypes.map(box=>
    '<span class="dot" style="background:#'+boxColor.get(box.box_profile_id).toString(16).padStart(6,'0')+'"></span>'+
    box.box_name+' ('+box.capacity_litre+' L)'
  ).join('<br>')+'<br><span class="muted"><span class="dot" style="background:#ffbe75"></span>Rear loading gate</span><br><span class="muted"><span class="dot" style="background:#67e6e1"></span>Deepest end</span>';

  const meshes=[];
  data.boxes.sort((a,b)=>a.sequence-b.sequence).forEach(b=>{{
    const geo=new THREE.BoxGeometry(b.l,b.h,b.w);
    const mat=new THREE.MeshStandardMaterial({{color:boxColor.get(b.box_profile_id),roughness:.52,metalness:.04,transparent:true,opacity:.92}});
    const mesh=new THREE.Mesh(geo,mat);
    // Optimizer X=length, Y=width, Z=height. Three.js Y is vertical.
    mesh.position.set(b.x+b.l/2,b.z+b.h/2,b.y+b.w/2);
    mesh.userData=b; scene.add(mesh);meshes.push(mesh);
    const outline=new THREE.LineSegments(new THREE.EdgesGeometry(geo),new THREE.LineBasicMaterial({{color:0xffffff,transparent:true,opacity:.72}}));
    mesh.add(outline);
  }});

  let shown=meshes.length; let timer=null;
  function updateShown(n){{shown=Math.max(0,Math.min(n,meshes.length));meshes.forEach((m,i)=>m.visible=i<shown);document.getElementById('stepLabel').textContent=`${{shown}} / ${{meshes.length}}`;}}
  updateShown(meshes.length);
  function stopPlay(){{if(timer){{clearInterval(timer);timer=null;}}}}
  document.getElementById('prev').onclick=()=>{{stopPlay();updateShown(shown-1)}};
  document.getElementById('next').onclick=()=>{{stopPlay();updateShown(shown+1)}};
  document.getElementById('restart').onclick=()=>{{stopPlay();updateShown(0)}};
  document.getElementById('all').onclick=()=>{{stopPlay();updateShown(meshes.length)}};
  document.getElementById('pause').onclick=stopPlay;
  document.getElementById('play').onclick=()=>{{stopPlay();if(shown>=meshes.length)updateShown(0);timer=setInterval(()=>{{if(shown>=meshes.length){{stopPlay();return;}}updateShown(shown+1)}},700)}};

  document.getElementById('view3d').onclick=set3D;document.getElementById('front').onclick=frontView;document.getElementById('side').onclick=sideView;document.getElementById('top').onclick=topView;document.getElementById('reset').onclick=set3D;

  const raycaster=new THREE.Raycaster();const pointer=new THREE.Vector2();
  renderer.domElement.addEventListener('click',e=>{{
    const rect=renderer.domElement.getBoundingClientRect();pointer.x=((e.clientX-rect.left)/rect.width)*2-1;pointer.y=-((e.clientY-rect.top)/rect.height)*2+1;raycaster.setFromCamera(pointer,camera);
    const hits=raycaster.intersectObjects(meshes.filter(m=>m.visible),false);
    if(!hits.length)return;const b=hits[0].object.userData;
    selectedPanel.innerHTML='<strong>Selected Box</strong><br><strong>'+b.box_label+'</strong><br>'+
      '<span class="muted">Customer:</span> '+b.customer_name+'<br>'+
      '<span class="muted">Order:</span> #'+b.order_id+' · Load sequence '+b.sequence+'<br>'+
      b.box_name+'<br><span class="muted">Size:</span> '+b.l+' × '+b.w+' × '+b.h+' cm<br>'+
      '<span class="muted">Loaded weight:</span> '+b.weight.toFixed(1)+' kg';
  }});

  function animate(){{requestAnimationFrame(animate);controls.update();renderer.render(scene,camera);labelRenderer.render(scene,camera)}}animate();
  window.addEventListener('resize',()=>{{camera.aspect=viewer.clientWidth/viewer.clientHeight;camera.updateProjectionMatrix();renderer.setSize(viewer.clientWidth,viewer.clientHeight);labelRenderer.setSize(viewer.clientWidth,viewer.clientHeight)}});
}} catch(err) {{
  console.error(err);
  const message = document.createElement('div');
  message.className = 'aq-notice';
  message.dataset.kind = 'error';
  message.setAttribute('role', 'alert');
  message.textContent = 'Three.js could not start. ' + String(err) + '. Check the browser connection. You can still use the saved loading sequence below.';
  selectedPanel.replaceChildren(message);
}}
}}
start();
</script>
</body>
</html>
"""

components.html(three_html, height=680, scrolling=False)

if is_preview:
    st.markdown("## Review Decision")
    st.info("Nothing has been saved yet. Approving will reserve the listed boxes, save this loading plan, and change its orders to Loaded.")
    back_col, approve_col = st.columns(2)
    with back_col:
        if st.button("Back to Optimization", icon=":material/arrow_back:", use_container_width=True):
            st.switch_page("pages/space_optimization.py")
    with approve_col:
        if st.button("Approve Plan & Mark Orders Loaded", icon=":material/check_circle:", type="primary", use_container_width=True):
            with st.spinner("Saving the approved loading plan..."):
                ok, message, plan_id = save_optimization(
                    preview_result, st.session_state.user_id, mark_loaded=True
                )
            if ok:
                st.session_state.selected_plan_id = plan_id
                st.session_state.optimization_preview = None
                st.session_state.pop("loading_plan_preview", None)
                flash("success", message)
                st.rerun()
            st.error(message)

st.markdown("## Loading Summary")
s1, s2, s3, s4 = st.columns(4)
weight_capacity_used = saved_weight_utilization(plan)
s1.metric("Weight Capacity Used", f"{weight_capacity_used:.1f}%")
s2.metric("Loaded Weight", f"{float(plan['total_weight']):,.1f} kg")
s3.metric("Remaining Weight", f"{float(plan['remaining_weight_capacity']):,.1f} kg")
s4.metric("Lorry Size", f"{plan['internal_length']:g}×{plan['internal_width']:g}×{plan['internal_height']:g} cm")

st.markdown("## Loading Sequence")
st.caption("Sequence 1 is loaded first at the deepest available end and continues toward the rear loading gate.")
sequence_df = pd.DataFrame([{
    "Sequence": p["sequence_number"],
    "Box Label": p.get("box_label"),
    "Order": f"#{p['order_id']}",
    "Customer": p.get("customer_name", "Customer"),
    "Box Size": f"{int(p.get('capacity_litre') or 0)}L",
    "Placed Size": f"{p['placed_length']:g} × {p['placed_width']:g} × {p['placed_height']:g} cm",
    "Weight": f"{p['loaded_weight']:.1f} kg",
} for p in plan["placements"]])
st.dataframe(sequence_df, use_container_width=True, hide_index=True)
