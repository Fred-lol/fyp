# AquaLoad Latest Requirements Implemented

This codebase incorporates the latest functional decisions made after the original `design.md`.

## Authentication and Account
- Customer registration redirects directly to Login after success.
- Login displays `Account created successfully. Please sign in.`
- Password rule remains minimum 8 characters only.
- Customer profile stores address, city, state and postcode.
- Light, Dark and System appearance preferences remain available to Customer and Staff.
- Logout text uses a dark navy font on the white button for readability.

## Staff Access
Warehouse Administrator, Loading Supervisor and Seafood Supplier keep their role names but intentionally have the **same operational functions and navigation**.

## Seafood Management
- Category is a controlled selection, not free text.
- Categories: Fish, Shellfish, Crustacean, Mollusk, Cephalopod, Other Seafood.
- Seafood stock is maintained in kg and shown to Customers.
- Customer orders cannot exceed available stock.
- Placing an order reserves/deducts stock; eligible cancellation restores it.

## Collection Point
- AquaLoad contains a configurable list of wholesale collection points around Malaysia for demonstration/configuration.
- New Customer orders are automatically assigned using the Customer's registered city/state.
- Example: a Customer in Kangar, Perlis is assigned to the Kangar Wholesale Collection Point.
- Staff may override the automatically assigned point.
- Space Optimization groups selected orders by the same collection point.

> The seeded collection-point list is AquaLoad demo/configuration data. For final deployment, replace it with the seafood supplier's approved real collection/wholesale sites.

## Order Status
- Only `Pending` is created automatically when the Customer places an order.
- Operational progression is manual and sequential:
  `Pending → Confirmed → Ready for Loading → Loaded → Completed`
- Cancellation is allowed only where configured.
- AquaLoad does not automatically pretend that seafood was prepared, loaded or collected.

## Standard Box Templates
Staff does not type box dimensions every time.

Preconfigured templates:
- 35L — 55 × 38 × 32 cm — maximum seafood weight 35 kg
- 50L — 65 × 43 × 38 cm — maximum seafood weight 50 kg
- 75L — 75 × 48 × 42 cm — maximum seafood weight 75 kg
- 100L — 90 × 55 × 50 cm — maximum seafood weight 100 kg

Staff chooses a size and adjusts physical inventory quantity.

## Automatic Box Recommendation
Customer Order Management displays total order kg and recommends standardized boxes based on:
1. Enough total kg capacity.
2. Available physical box inventory.
3. Fewest boxes.
4. Least unused capacity.
5. Larger standardized boxes as final tie-breaker.

Examples:
- 50 kg → 1 × 50L.
- 100 kg → 1 × 100L is best; 2 × 50L appears as an alternative.
- AquaLoad avoids recommending many 35L boxes when fewer larger boxes are suitable.
- Staff can accept the recommendation or manually select a valid combination.

## Space Optimization
- Select collection point first.
- Select available lorry.
- Select Ready for Loading orders going to that same point.
- Review standardized box requirements.
- Generate compact candidate-position 3D plan.
- Validate lorry boundary, no overlap, full support, heavy-on-light stacking and maximum weight.
- Save exact X/Y/Z placements.

## 3D Loading Plan
- Three.js uses the saved placement coordinates; it does not invent a new arrangement.
- Import-map setup fixes the previous blank OrbitControls/Three.js module issue.
- Staff can rotate, zoom and pan.
- Views: 3D, Front, Side, Top, Reset.
- Boxes are colored by Order.
- Clicking a box shows Order, size, weight, coordinates and loading sequence.
- Loading sequence controls: Previous, Next, Play, Pause, Restart, Show All.

## REST API Live Tracking
- `tracking_api.py` implements AquaLoad's planned REST API with FastAPI and JSON.
- Driver/Staff GPS sharing page: `/driver`.
- Customer tracking endpoint verifies the order belongs to the supplied Customer ID.
- Customer Track Order page refreshes latest lorry location approximately every 30 seconds.
- Collection point is shown as the destination on the map.
- A separate FastAPI process must run for live tracking.

## Reports & Analytics
Reports answer: **What happened in this loading plan and was it valid?**
Analytics answer: **How well are loading operations performing overall?**

Useful report information includes:
- lorry and collection point
- orders included
- total seafood / loaded weight
- total boxes
- box-size breakdown
- space used / remaining
- weight used / remaining
- validation checks
- operational utilization insight
- loading sequence

Useful analytics include:
- total loading plans
- average and best space utilization
- total boxes loaded
- utilization by plan
- loaded weight by plan
- box-size usage
- lorry usage
- collection-point usage

Raw database-style labels and unnecessary/fake metrics are avoided.

## Payment UI — latest requirement

- Payment is a UI/demo flow only. No Stripe or real payment gateway is required.
- Order Seafood now continues to an Order Review & Payment page.
- The payment page supports Credit / Debit Card, Online Banking, and E-Wallet UI states.
- Card fields are never stored or sent to an external service.
- Completing the demonstration checkout creates the real Pending AquaLoad order, deducts seafood stock, assigns the collection point, and records a local payment reference/status for UI consistency.
- My Orders and Staff Customer Order Management show the payment status and amount.

## Appearance — latest requirement

- Light mode uses a bright white background with white cards and dark navy text.
- Dark mode uses high-contrast light text with visible placeholders, labels, controls, cards, tabs and sidebar navigation.
- System mode continues to follow the browser/operating-system appearance.
- The Forgot Password page remains a bright light/public page and no longer shows the implementation/FYP explanatory sentence at the bottom.
