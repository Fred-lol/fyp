# AquaLoad redesign verification

Local implementation; not pushed or deployed.

## Active code changed
- `homepage.py`: replaces the old 3,000-line landing page with a two-column hero, sample plan and three capabilities.
- `components/public_shell.py`: shared `render_homepage_header`, `render_homepage_footer`, `render_sample_plan`; used by Home, About and Who We Serve. Responsive navigation and theme tokens.
- `components/commerce.py`: reusable `product_card`, responsive 4/2/1 grid, aligned images/prices/controls and compact stock indicators.
- `pages/order_seafood.py`: `ordering_workspace`, cart actions and fresh-stock validation; old cards removed.
- `components/charts.py`: `capacity_chart`, `bar_chart`, `chart_style`, `render_chart`; Plotly replaces all Altair report charts.
- `pages/reports_analytics.py`: `render_reports`, `render_analytics`; report search, seven Plotly visualizations across both tabs, separate insight metrics.
- `pages/payment.py`: replaces the active checkout and unreachable duplicate with `render_payment`, `submit_demo_order`, inline errors and session-only display snapshot.
- `services/payment_service.py`: credential-free demo validation, Malaysian mobile validation, lightweight summary query, atomic/idempotent submission. FPX demo bank subset checked against PayNet participating-bank list.
- `services/order_service.py`: shared transaction support, finite quantities, deterministic product locking, Simulated payment compatibility.
- `pages/manage_orders.py`, `pages/my_orders.py`, `pages/payment_success.py`: support explicitly Simulated payment records without breaking fulfillment eligibility.
- `components/navigation.py`: session cleanup includes new checkout state; compact session-expired layout retained.
- `components/theme.py`, `components/design_system.py`: remove obsolete image rules, simplify action styling and correct metric text sizing. Shared `components/alert_theme.py` owns semantic notification palettes.
- `requirements.txt`: Plotly 6 and Streamlit 1.66 minimum.

## Evidence
- Full automated suite: 58 passed, 9 skipped (dedicated legacy test database unavailable).
- Ten real PostgreSQL transaction tests use connection-local temporary tables, pg_temp-only search path, and rollback. No production orders or inventory modified.
- Four Streamlit AppTest scenarios cover all methods, invalid/missing inputs, successful simulated submission and redirect. Summary fetched once despite method/field reruns.
- Normal local app at port 8501: Home, About and Who We Serve each render shared 80px header, one footer, no exception.
- Browser screenshots in this directory use actual page renderers. Authenticated-page browser harness bypasses login only and reads existing Supabase records; it does not submit production orders.
- Browser matrix result is recorded separately in browser-results.json when complete. Screenshots cover desktop/mobile, Light/Dark and semantic messages.
- Compile checks and git diff whitespace check passed.

## Limitations
- No real financial transaction is performed. New payments are recorded as Simulated.
- No production order was submitted for browser testing; successful writes and rollback were verified in isolated PostgreSQL temporary tables instead.
- No full regression of optimization, tracking or third-party APIs was performed.
- Local branch main and remote main were both at 16e8153 before these uncommitted changes. render.yaml does not specify a branch; Render dashboard/build logs were not accessible or verified. These local changes have not been deployed.
- Before-state comparison uses the user-provided screenshots; no automated baseline screenshot was captured before editing.
- Browser timing includes explicit settling waits and is not a production performance benchmark. Method switching now performs zero product-summary queries after initial session load, verified by AppTest.

Sources: https://knowledgebase.paynet.my/hc/en-us/articles/49685463748121-Which-banks-participate-in-FPX and https://mcmc.gov.my/skmmgovmy/media/General/pdf/SKMM_11eng.pdf

Final browser matrix: 102 checks passed. Payment-method switch checks took 677-679 ms including a fixed 650 ms settling wait; these are not network latency benchmarks.
