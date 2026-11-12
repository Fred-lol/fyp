# AquaLoad

AquaLoad is a Streamlit-based seafood ordering and insulated fish storage box lorry-loading optimization FYP system.

## Main stack
- Python
- Streamlit
- Supabase PostgreSQL
- Google OR-Tools + custom 3D placement/constraint logic
- NumPy
- Three.js
- FastAPI REST API + JSON for live lorry tracking

## Folder start
Run the application from the project root, not from an individual page.

```powershell
cd C:\fyp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Set SUPABASE_DB_URL in .env (keep the real value private)
python setup_database.py
python -m streamlit run homepage.py
```

If PowerShell blocks activation for the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Live tracking REST API
Open a second PowerShell terminal while Streamlit remains running:

```powershell
cd C:\fyp
.\.venv\Scripts\Activate.ps1
python -m uvicorn tracking_api:app --reload --port 8000
```

Useful tracking URLs:
- API health: `http://127.0.0.1:8000/api/health`
- FastAPI documentation: `http://127.0.0.1:8000/docs`
- Driver/Staff GPS sharing page: `http://127.0.0.1:8000/driver`

The Driver page uses browser `navigator.geolocation` and sends GPS JSON to AquaLoad through `POST /api/location/update` approximately every 25–30 seconds. Browser GPS normally requires HTTPS when opened from another physical phone; localhost is allowed for development.

## Staff accounts
All three Staff roles intentionally have the same application functions.

```text
Warehouse Administrator
Email: admin.aquaload@gmail.com
Password: Admin12345

Loading Supervisor
Email: supervisor.aquaload@gmail.com
Password: Supervisor12345

Seafood Supplier
Email: supplier.aquaload@gmail.com
Password: Supplier12345
```

## Demo Customer

```text
Email: demo.customer@gmail.com
Password: Customer12345
Location: Kangar, Perlis
```

The demo Customer has orders and saved loading-plan data so the Staff pages, 3D Loading Plan, Reports and Analytics can be viewed immediately.

## Important behavior
- Customer registration redirects to Login after successful account creation.
- Seafood category is selected from controlled categories.
- Seafood stock is real application inventory; orders reserve/deduct it.
- Box dimensions come from fixed 35L/50L/75L/100L templates.
- Customer Order Management recommends box combinations from total order kg and available box inventory.
- New orders receive a configured collection point automatically from the Customer's registered city/state; Staff can override it.
- Only `Pending` is automatic. Operational statuses are manually confirmed by Staff.
- Space Optimization only shows `Ready for Loading` orders and groups them by collection point.
- 3D visualization uses saved X/Y/Z placements from the optimizer.
- Three.js is loaded using an import map so `OrbitControls` resolves the `three` module correctly.
- Reports use saved valid plans as their source of truth. Analytics use real saved plan/report data only.

## Three.js note
The 3D viewer loads Three.js from jsDelivr. If a network/browser blocks the CDN, the page shows a visible error rather than silently displaying an empty dark panel. The saved loading-sequence table below the viewer remains available.

## Seeded collection points
Collection points in this FYP are configurable AquaLoad demonstration/operational points for Malaysian cities/state capitals. Replace them with the seafood supplier's verified wholesale/collection sites for final deployment.

## Tests
Run:

```powershell
pytest -q
```

The tests cover password hashing, stock reservation/restoration, theme persistence, optimizer validity, automatic Perlis/Kangar collection assignment, box recommendations and manual status progression. Database integration tests require a separate `AQUALOAD_TEST_DATABASE_URL`; never use a production URL for tests.

## Live lorry tracking quick start

AquaLoad live tracking uses a FastAPI REST API in addition to Streamlit.

### Start both together

```powershell
cd C:\fyp
.\.venv\Scripts\Activate.ps1
.\run_aquaload.ps1
```

`run_aquaload.ps1` opens the Tracking REST API on port 8000 and then starts Streamlit.

### Or start separately

Terminal 1:

```powershell
python -m streamlit run homepage.py
```

Terminal 2:

```powershell
.\run_tracking_api.ps1
```

When the API is running, Staff can open **Lorry Location Tracking** and use **Open Driver GPS Sharing Page**. The device travelling with the lorry selects the lorry and shares browser GPS. A Customer sees the location only when their order is included in a saved loading plan using that lorry.

For FYP testing without a phone, the Staff Lorry Location Tracking page also includes a clearly labelled **Development GPS Simulator**. It posts manually entered coordinates through the same REST API so the complete tracking flow can be demonstrated without pretending those coordinates came from a real GPS device.

## Payment UI

AquaLoad includes a simulated payment page for FYP UI demonstration. It does not use Stripe or another real payment gateway and does not store entered card/bank credentials. The successful UI flow creates the Pending order, records a local AquaLoad payment reference, deducts stock, and continues the normal order workflow.
