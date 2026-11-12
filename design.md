# AquaLoad — Complete System Design Specification

**System:** AquaLoad — Space Optimization System for Insulated Fish Storage Box Loading in Lorry  
**Tagline:** *Smarter Loads · Fresher Seafood*  
**Primary stack:** Python, Streamlit, Supabase PostgreSQL, Google OR-Tools, NumPy, Three.js, REST/JSON where required  
**Purpose:** Define the complete UI/UX, navigation, role, page, data, validation, optimization, reporting, and implementation design for AquaLoad.

---

# 1. Current Baseline — Keep These Three Pages

The following pages are already accepted and should remain as the visual baseline:

1. `homepage.py`
2. `pages/login.py`
3. `pages/register.py`

Future pages must follow the same AquaLoad visual identity and should not introduce an unrelated design style.

## 1.1 Preserve these current decisions

- AquaLoad logo and tagline
- navy / teal / cyan seafood-logistics color palette
- soft light backgrounds
- rounded cards and inputs
- centered Login and Register layouts
- clear Customer / Staff separation
- Malaysian coastal identity on Homepage
- no unnecessary prototype labels in the real UI
- no internal iframe scrollbar for normal pages

## 1.2 Important current integration gap

Customer registration and login use the Supabase PostgreSQL-backed `users` table with hashed passwords, so a newly registered Customer can immediately log in.

---

# 2. Product Overview

AquaLoad is a web-based seafood ordering and lorry loading optimization system. It combines a simple Customer experience with an operational Staff experience.

## 2.1 Customer experience

Customers use AquaLoad to:

- register
- log in
- browse available seafood
- place seafood orders
- view their own orders
- update eligible orders
- cancel eligible orders
- track order status
- manage profile information
- change password

The Customer side must stay simple and seafood-focused. Technical optimization terms should not dominate Customer pages.

## 2.2 Staff operations experience

Authorized Staff use AquaLoad to:

- manage user accounts
- review Customer orders
- confirm orders
- update order information and status
- manage lorry profiles
- manage insulated fish storage box profiles
- generate optimized loading plans
- regenerate and save plans
- view 3D loading arrangements
- view loading summary and loading sequence
- mark eligible orders as loaded
- generate loading reports
- filter and download reports
- review loading analytics

---

# 3. User Roles

AquaLoad has four roles.

## 3.1 Customer

Permissions:

- self-register
- normal login
- update own profile
- change own password
- browse seafood
- place order
- view own orders
- update eligible own orders
- cancel eligible own orders
- track own order status

Customer must never access Staff-only pages.

## 3.2 Warehouse Administrator

Primary operational role.

Permissions:

- manage user accounts
- manage Customer orders
- confirm orders
- update operational order information
- manage lorry profiles
- manage box profiles
- generate loading plans
- regenerate loading plans
- save loading plans
- view 3D loading plans
- generate reports
- view reports and analytics

## 3.3 Loading Supervisor

Execution-focused role.

Permissions:

- view relevant orders
- view loading plans
- view 3D arrangement
- view loading summary
- view loading sequence
- update permitted loading-related status
- mark eligible orders as loaded

## 3.4 Seafood Supplier

Oversight-focused role.

Permissions:

- access Staff Dashboard
- review loading reports
- filter reports
- download permitted reports
- review loading analytics

---

# 4. Role-Based Access Matrix

| Function | Customer | Warehouse Administrator | Loading Supervisor | Seafood Supplier |
|---|---:|---:|---:|---:|
| Register own account | Yes | No | No | No |
| Normal login | Yes | Yes | Yes | Yes |
| Staff Portal login | No | Yes | Yes | Yes |
| View own profile | Yes | Yes | Yes | Yes |
| Change own password | Yes | Yes | Yes | Yes |
| Browse seafood | Yes | Optional | Optional | Optional |
| Place seafood order | Yes | No | No | No |
| View own orders | Yes | No | No | No |
| Track own order | Yes | No | No | No |
| Manage users | No | Yes | No | No |
| Manage Customer orders | No | Yes | Limited | Read-only if required |
| Update operational status | No | Yes | Yes, where permitted | No |
| Manage lorry profiles | No | Yes | No | No |
| Manage box profiles | No | Yes | No | No |
| Generate loading plan | No | Yes | No | No |
| Regenerate / save plan | No | Yes | No | No |
| View 3D loading plan | No | Yes | Yes | Optional read-only |
| View loading sequence | No | Yes | Yes | Optional |
| Generate reports | No | Yes | Limited if required | Read-only / download |
| View analytics | No | Yes | Limited | Yes |

Database role is always the final authority.

---

# 5. Authentication Design

## 5.1 Customer email convention

Example:

`customer@gmail.com`

Customers register publicly through `register.py`.

## 5.2 Staff email convention

Recommended examples:

- `admin.aquaload@gmail.com`
- `warehouse01.aquaload@gmail.com`
- `supervisor01.aquaload@gmail.com`
- `supplier.aquaload@gmail.com`

The `.aquaload` convention is only a naming convention. It must never grant permission by itself.

## 5.3 Normal Login behavior

```text
Enter email + password
        ↓
Authenticate account
        ↓
Check account status
        ↓
Read stored role
        ↓
Customer → Customer Dashboard
Warehouse Administrator → Staff Dashboard
Loading Supervisor → Staff Dashboard
Seafood Supplier → Staff Dashboard
```

## 5.4 Staff Portal behavior

```text
Select Staff Portal
        ↓
Enter email + password
        ↓
Authenticate
        ↓
Role is Staff?
   ├── Yes → Staff Dashboard
   └── No  → Reject access
```

Recommended rejection message:

> This account is not authorized to access the Staff Portal.

## 5.5 Registration behavior

Public registration creates only Customers:

- `role = Customer`
- `status = Active`

Staff accounts are created separately by authorized personnel.

## 5.6 Password rule

Current rule:

- minimum 8 characters

Do not require uppercase, lowercase, number, or symbol unless requirements change.

Passwords must be hashed and salted before storage.

---

# 6. Complete Page Inventory

The shared Login page includes Customer mode and Staff Portal mode, so the system needs about **18 main pages**.

## Public / Authentication

1. Homepage
2. Login / Staff Portal Login
3. Customer Registration
4. Forgot / Reset Password

## Customer

5. Customer Dashboard
6. Order Seafood
7. My Orders
8. Track Order Status
9. My Profile / Change Password

## Staff

10. Staff Dashboard
11. User Account Management
12. Customer Order Management
13. Order Status / Tracking Management
14. Lorry Profile Management
15. Insulated Fish Storage Box Management
16. Space Optimization
17. 3D Loading Visualization
18. Loading Reports & Analytics

Do not create a new page for every Add/Edit/Delete action. Related CRUD functions should stay inside the relevant management page.

---

# 7. Recommended Folder Structure

```text
C:\fyp\
│
├── homepage.py
├── AquaLoad.png
├── database/migrations/001_initial.sql
├── requirements.txt
├── design.md
│
├── .streamlit\
│   └── config.toml
│
├── pages\
│   ├── login.py
│   ├── register.py
│   ├── forgot_password.py
│   ├── customer_dashboard.py
│   ├── order_seafood.py
│   ├── my_orders.py
│   ├── track_order.py
│   ├── profile.py
│   ├── staff_dashboard.py
│   ├── manage_users.py
│   ├── manage_orders.py
│   ├── order_status_management.py
│   ├── lorry_profiles.py
│   ├── box_profiles.py
│   ├── space_optimization.py
│   ├── loading_visualization.py
│   └── reports_analytics.py
│
├── components\
│   ├── navigation.py
│   ├── cards.py
│   ├── tables.py
│   ├── dialogs.py
│   └── status_badges.py
│
├── services\
│   ├── auth_service.py
│   ├── user_service.py
│   ├── order_service.py
│   ├── lorry_service.py
│   ├── box_service.py
│   ├── optimization_service.py
│   ├── report_service.py
│   └── analytics_service.py
│
├── database\
│   ├── db.py
│   ├── schema.py
│   └── seed.py
│
├── optimization\
│   ├── optimizer.py
│   ├── constraints.py
│   ├── scoring.py
│   └── validation.py
│
└── assets\
    ├── seafood\
    ├── icons\
    └── generated\
```

---

# 8. AquaLoad Visual Design System

## 8.1 Colors

| Token | Hex | Usage |
|---|---|---|
| Navy | `#062e55` | dark brand color |
| Dark Navy | `#031c35` | footer / dark operational surfaces |
| Malaysia Blue | `#003f72` | secondary brand accent |
| Ocean Blue | `#087ab0` | links / actions |
| Teal | `#009c9a` | primary accent |
| Cyan | `#00aeb7` | active controls / gradients |
| Seafoam | `#dff7f4` | soft states |
| Light Cyan | `#ebfafa` | light card backgrounds |
| Sand | `#f4ead9` | Malaysian coastal accent |
| Gold | `#d8a441` | small accent |
| Coral | `#df7055` | warning/destructive accent |
| Main Text | `#173b58` | headings/body |
| Muted Text | `#647d90` | descriptions |
| Border | `#dceaf0` | cards / inputs |
| Background | `#f7fbfd` | default page background |

## 8.2 Main button gradient

```css
background: linear-gradient(
    135deg,
    #087ead,
    #0db4b9
);
```

## 8.3 Dark staff/optimization panels

```css
background: linear-gradient(
    145deg,
    #062f55,
    #064c68
);
```

## 8.4 Typography

```css
font-family:
    Inter,
    "Segoe UI",
    Arial,
    Helvetica,
    sans-serif;
```

Recommended sizes:

| Type | Size |
|---|---:|
| Homepage hero | 48–55px |
| Main page title | 38–44px |
| Section heading | 28–36px |
| Card title | 18–24px |
| Normal body | 13–16px |
| Supporting label | 10–12px |
| Table body | 12–14px |

## 8.5 Border radius

- major card: 20–25px
- form card: 20–24px
- standard card: 14–18px
- input: 10–12px
- primary button: 12–14px
- secondary button: 10–12px
- badge: 30px

## 8.6 Standard shadow

```css
box-shadow:
    0 16px 42px
    rgba(9, 54, 75, 0.075);
```

## 8.7 Spacing scale

- 4px micro
- 8px tight
- 12px control gap
- 16px normal
- 24px card spacing
- 32px section internal spacing
- 48px major section gap
- 64px+ page section gap

---

# 9. Global UI Rules

## Customer side

Must feel:

- simple
- fresh
- seafood-focused
- non-technical
- easy to navigate

## Staff side

Must feel:

- operational
- structured
- information-dense but readable
- dashboard-oriented
- focused on status and actions

## One primary action per page

Examples:

- Login → `Login to AquaLoad`
- Register → `Create Account`
- Order Seafood → `Review Order`
- Optimization → `Generate Optimized Plan`
- Reports → `Generate Report`

## Never show development text in real UI

Do not show:

- UI Prototype
- Demo account
- Page will be connected next
- Temporary feature
- Internal implementation notes

---

# 10. Navigation Design

## 10.1 Public navigation

Keep Homepage navigation similar to current accepted design:

- Home
- Order Seafood
- About AquaLoad
- Who We Serve
- Staff Portal

## 10.2 Authenticated Customer navigation

Recommended:

- Dashboard
- Order Seafood
- My Orders
- Track Order
- My Profile
- Logout

## 10.3 Staff navigation

Recommended custom sidebar:

```text
AquaLoad Operations

Dashboard
Customer Orders
Order Status
Lorry Profiles
Box Profiles
Space Optimization
3D Loading Plan
Reports & Analytics

Profile
Logout
```

Only show menu items permitted for the current role.

---

# 11. Page 1 — Homepage

**File:** `homepage.py`  
**Status:** Keep current accepted design.

Main sections:

1. sticky navbar
2. hero
3. Malaysian seafood/logistics tags
4. loading optimization preview
5. Customer vs Staff section
6. Who AquaLoad Serves
7. About AquaLoad
8. footer

Customer card functions:

- Browse Seafood
- Place Seafood Order
- View My Orders
- Update / Cancel Order
- Track Order Status
- Manage Profile

Staff card functions:

- Manage Customer Orders
- Lorry Profiles
- Storage Box Profiles
- Space Optimization
- 3D Loading Plan
- Reports & Analytics

Do not add fake business metrics or unsupported claims.

---

# 12. Page 2 — Login / Staff Portal Login

**File:** `pages/login.py`  
**Status:** Keep current centered layout.

## Customer / normal mode

Header:

- `CUSTOMER & STAFF ACCESS`
- `Login to AquaLoad`

Controls:

- Customer Login
- Staff Portal
- Email Address
- Password
- Login to AquaLoad
- Forgot Password
- Create Account

## Staff mode

Header:

- `AQUALOAD STAFF ACCESS`
- `Staff Portal Login`

Controls:

- Customer Login
- Staff Portal
- Email Address
- Password
- Login to Staff Portal
- Forgot Password

Do not show Create Account in Staff mode.

---

# 13. Page 3 — Customer Registration

**File:** `pages/register.py`  
**Status:** Keep current centered layout.

Fields:

- Full Name
- Email Address
- Phone Number
- Password
- Confirm Password

Validation:

- Full Name required
- valid email
- email unique
- staff-style email rejected from public registration
- phone required and valid
- password at least 8 characters
- confirm password must match

Password hint appears only while entering Password.

Bottom text:

`Already have an AquaLoad account?`

This text is clickable. Do not use a large Back button.

---

# 14. Page 4 — Forgot / Reset Password

**Suggested file:** `pages/forgot_password.py`

Use the same centered visual pattern as Login and Register.

## Initial view

Title:

`Reset Your Password`

Description:

`Enter your registered AquaLoad email address to continue.`

Input:

- Email Address

Button:

- Continue

Text link:

- Return to Login

Use the exact reset mechanism approved for the final project. Do not simulate an email if real email sending is not implemented.

New password rule remains minimum 8 characters.

---

# 15. Page 5 — Customer Dashboard

**Suggested file:** `pages/customer_dashboard.py`

Header example:

`Welcome back, [Customer Name]`

Main cards:

### Order Seafood

`Browse available seafood and place a new order.`

### My Orders

Show:

- active order count
- latest order ID
- latest status

### Track Order

Show latest active order and current status.

## Recent Orders

| Order ID | Order Date | Items | Status | Action |
|---|---|---:|---|---|

Empty state:

> You have not placed any seafood orders yet.

Button:

`Order Seafood`

---

# 16. Page 6 — Order Seafood

**Suggested file:** `pages/order_seafood.py`

Title:

`Order Seafood`

Description:

`Browse available seafood and prepare your order.`

## Product cards

Show real available data such as:

- seafood name
- image
- category/type
- unit
- price if part of final requirements
- availability
- quantity selector

Do not show fake stock counts, ratings, sales, or reviews.

## Search / Filter

Recommended:

- Search Seafood
- Category
- Availability
- Clear Filters

## Order Summary

Show:

- selected items
- quantity
- total quantity
- price subtotal if applicable
- remove item

Primary button:

`Review Order`

Validation:

- at least one selected item
- quantity > 0
- item still available
- required information complete

---

# 17. Page 7 — My Orders

**Suggested file:** `pages/my_orders.py`

Title:

`My Orders`

Filters:

- All
- Active
- Completed
- Cancelled

Use exact approved statuses.

Each row/card:

- Order ID
- Order Date
- seafood summary
- total quantity
- current status
- last updated
- actions

Possible actions:

- View Details
- Update Order
- Cancel Order
- Track Status

Update/Cancel only appear when the order is eligible.

Cancellation requires confirmation.

---

# 18. Page 8 — Track Order Status

**Suggested file:** `pages/track_order.py`

Title:

`Track Order Status`

Show:

- Order ID
- Order Date
- Current Status
- Last Updated
- Collection information when available

Use a timeline:

```text
● Previous Status
│
● Current Status
│
○ Next Status
```

Use exact project status vocabulary.

Status history comes from `OrderStatusHistory`.

---

# 19. Page 9 — My Profile / Change Password

**Suggested file:** `pages/profile.py`

Profile data:

- Full Name
- Email
- Phone
- Role

Editable by Customer:

- Full Name
- Phone

Change Password fields:

- Current Password
- New Password
- Confirm New Password

Rule:

- current password correct
- new password at least 8 characters
- confirmation matches

---

# 20. Page 10 — Staff Dashboard

**Suggested file:** `pages/staff_dashboard.py`

Role-aware page.

## Warehouse Administrator

Summary cards:

- Customer Orders
- Orders Awaiting Action
- Available Lorries
- Active Box Profiles
- Saved Loading Plans
- Recent Reports

Quick actions:

- Manage Orders
- Manage Lorries
- Manage Boxes
- Generate Loading Plan

## Loading Supervisor

Cards:

- Plans Ready for Loading
- Orders Ready for Loading
- Current Loading Tasks
- Recently Loaded Orders

Quick actions:

- View 3D Loading Plan
- View Loading Sequence
- Update Loading Status

## Seafood Supplier

Cards:

- Recent Loading Plans
- Recent Reports
- Average Space Utilization
- Report Period

Quick actions:

- View Reports
- View Analytics

All metrics must be calculated from real data.

---

# 21. Page 11 — User Account Management

**Suggested file:** `pages/manage_users.py`  
**Role:** Warehouse Administrator

Title:

`User Account Management`

Summary cards:

- Active Customers
- Active Staff
- Inactive Accounts

Table columns:

- User ID
- Full Name
- Email
- Phone
- Role
- Status
- Created Date
- Actions

Filters:

- name/email search
- role
- status

Never show password hashes or salts.

---

# 22. Page 12 — Customer Order Management

**Suggested file:** `pages/manage_orders.py`

Title:

`Customer Order Management`

Table:

- Order ID
- Customer
- Order Date
- Item Count
- Current Status
- Collection Point
- Actions

Filters:

- Order ID
- Customer
- Status
- Date Range

Order detail panel:

- Customer information
- seafood items
- quantities
- status
- status history
- collection information
- loading-related information where relevant

Main actions:

- Confirm Order
- Set / Update Collection Point
- Update Status
- View Tracking History

---

# 23. Page 13 — Order Status / Tracking Management

**Suggested file:** `pages/order_status_management.py`

Table:

- Order ID
- Customer
- Current Status
- Last Updated
- Loading Plan if any
- Action

Status update uses a controlled dropdown, not free text.

Loading Supervisor sees `Mark as Loaded` only when the order is eligible.

Require confirmation before irreversible status changes.

---

# 24. Page 14 — Lorry Profile Management

**Suggested file:** `pages/lorry_profiles.py`

Title:

`Lorry Profile Management`

Table fields:

- Lorry ID
- Plate Number
- Internal Length
- Internal Width
- Internal Height
- Maximum Weight
- Status
- Last Updated
- Actions

The displayed lorry identifier should prominently use the plate number.

Add/Edit form:

- Plate Number
- Internal Length
- Internal Width
- Internal Height
- Maximum Load Weight
- Status

Always show units.

Example:

- Length (cm)
- Width (cm)
- Height (cm)
- Max Weight (kg)

Validation:

- plate required
- no duplicate plate
- dimensions > 0
- max weight > 0
- numeric values only

Actions:

- Add
- Edit
- Set Status
- Delete

Delete requires confirmation.

---

# 25. Page 15 — Insulated Fish Storage Box Management

**Suggested file:** `pages/box_profiles.py`

Title:

`Insulated Fish Storage Box Management`

Table:

- Box ID
- Box Name / Type
- Length
- Width
- Height
- Weight-related value required by algorithm
- Quantity / availability if supported
- Status
- Actions

Add/Edit form must match optimization inputs.

Validation:

- dimensions > 0
- weight >= 0
- name required
- numeric values only

Actions:

- Add
- Edit
- Sort
- Set Status
- Delete

---

# 26. Page 16 — Space Optimization

**Suggested file:** `pages/space_optimization.py`

This is a core FYP page.

Title:

`3D Space Optimization`

Description:

`Generate a suitable loading arrangement for confirmed seafood orders using available lorry capacity and insulated fish storage box constraints.`

## Step 1 — Select Lorry

Show:

- Plate Number
- Dimensions
- Maximum Weight
- Status

Only eligible lorries selectable.

## Step 2 — Select Orders

Show eligible orders:

- checkbox
- Order ID
- Customer
- required boxes
- estimated weight
- priority if defined

## Step 3 — Review Box Requirements

Show:

- Box Type
- Dimensions
- Quantity
- Weight
- Related Order

## Step 4 — Generate Plan

Primary button:

`Generate Optimized Plan`

Pre-validation:

- lorry selected
- order selected
- dimensions valid
- box profiles available
- quantities valid
- weight information available
- lorry active
- orders eligible

During generation:

`Generating optimized loading plan...`

Result summary:

- Plan ID
- Lorry
- Orders
- Total Boxes
- Total Box Volume
- Lorry Volume
- Used Volume
- Remaining Volume
- Space Utilization / VFR
- Total Weight
- Remaining Weight Capacity
- Constraint Validation

Buttons:

- View 3D Plan
- Regenerate
- Save Plan

---

# 27. Optimization Algorithm Design

Treat the problem as a constrained 3D bin-packing / placement problem.

## Inputs

### Lorry

- internal length
- internal width
- internal height
- maximum weight

### Box instance

- box profile
- length
- width
- height
- loaded weight
- associated order
- orientation options if allowed
- stacking properties if defined

## Boundary constraint

```text
x >= 0
y >= 0
z >= 0

x + placed_length <= lorry_length
y + placed_width  <= lorry_width
z + placed_height <= lorry_height
```

## No-overlap constraint

No two boxes may occupy the same 3D region.

## Maximum weight

```text
sum(box_weights) <= lorry_max_weight
```

## Stacking

Apply project-defined stacking constraints, for example when required:

- heavy boxes not on unsuitable lighter boxes
- no unsupported placement
- stack height within lorry height
- stable placement

## Weight distribution

Avoid strongly unbalanced loading where the final project rules require balance consideration.

## Objective

Primary:

- produce valid arrangement
- maximize useful space utilization

Secondary evaluation may include:

- lower unused volume
- stable stacking
- reasonable weight distribution

## Heuristic ordering

Possible pre-sorting:

- descending volume
- descending footprint
- descending weight
- operational priority

The actual heuristic must remain consistent with the report.

## OR-Tools

Use Google OR-Tools for decision/constraint solving where suitable. Custom geometry constraints are still required.

## NumPy

Use for:

- volume calculations
- geometric operations
- weight-distribution calculations
- coordinate arrays
- report metrics

---

# 28. Loading Plan Data

`LoadingPlan` should store:

- Plan ID
- Lorry ID
- Created By
- Created Date/Time
- Plan Status
- Total Boxes
- Total Volume
- Used Volume
- Remaining Volume
- Space Utilization / VFR
- Total Weight
- Remaining Weight Capacity
- Validation result

Each `BoxPlacement` should store:

- Placement ID
- Plan ID
- Box Profile ID
- Order ID
- Box Instance Number
- X
- Y
- Z
- Placed Length
- Placed Width
- Placed Height
- Orientation
- Sequence Number

Stored coordinates must be the exact coordinates used in 3D visualization.

---

# 29. Page 17 — 3D Loading Visualization

**Suggested file:** `pages/loading_visualization.py`

Technology:

- Streamlit page
- Three.js rendering
- JSON placement data

Layout:

```text
Plan #XXXX      Lorry ABC1234      Status
────────────────────────────────────────────
|                  | Loading Summary         |
|   3D Lorry View  | Total Boxes             |
|                  | Used Volume             |
|                  | Utilization             |
|                  | Total Weight            |
────────────────────────────────────────────
Loading Sequence
```

Controls:

- rotate
- zoom
- pan
- reset view
- labels on/off if useful

Each box should represent:

- proportional dimensions
- box type
- order association
- loading sequence

Use consistent colors. Do not randomly recolor boxes every refresh.

Box details on click/hover:

- Box ID
- Order ID
- Type
- Dimensions
- Weight
- Position
- Sequence

Loading sequence table:

| Sequence | Box | Order | Position | Box Type |
|---:|---|---|---|---|

Never display `Optimized` if generation failed.

---

# 30. Page 18 — Loading Reports & Analytics

**Suggested file:** `pages/reports_analytics.py`

Use two tabs:

1. Reports
2. Analytics

## Reports tab

Filters:

- Date Range
- Lorry
- Plan ID
- Report Status if used

Table:

- Report ID
- Plan ID
- Lorry
- Generated Date
- Total Boxes
- Space Utilization
- Total Weight
- Actions

Actions:

- View
- Download

Report detail:

- Report ID
- Plan ID
- Lorry Plate
- Generated Date
- Generated By
- Number of Orders
- Total Boxes
- Lorry Volume
- Used Volume
- Remaining Volume
- VFR
- Total Weight
- Remaining Weight Capacity
- Orders
- Placement Summary

## Analytics tab

Real metrics only:

- Total Loading Plans
- Average Space Utilization
- Highest Space Utilization
- Average Box Count per Plan
- Most Frequently Used Lorry

Possible charts:

- Space Utilization by Plan
- Utilization Over Time
- Plans by Lorry
- Box Count Over Time

Do not use fake values.

---

# 31. Database Design

Supabase PostgreSQL remains the primary database.

## 31.1 users

```text
user_id
full_name
email
phone_number
password_hash
password_salt
role
status
created_at
updated_at
```

Rules:

- primary key user_id
- unique email
- controlled role
- controlled status

## 31.2 seafood_products

Needed if AquaLoad stores browseable seafood product data.

```text
product_id
product_name
category
description
unit
price                 # only if pricing is part of final requirements
availability_status
image_path
created_at
updated_at
```

## 31.3 seafood_orders

```text
order_id
customer_id
order_date
status
collection_point
created_at
updated_at
```

## 31.4 order_items

```text
order_item_id
order_id
product_id
quantity
unit
```

## 31.5 order_status_history

```text
history_id
order_id
status
updated_by
updated_at
note
```

## 31.6 lorry_profiles

```text
lorry_id
plate_number
internal_length
internal_width
internal_height
max_weight
status
created_at
updated_at
```

## 31.7 box_profiles

```text
box_profile_id
box_name
length
width
height
weight_parameter
status
created_at
updated_at
```

Store only box fields actually used by the final algorithm.

## 31.8 loading_plans

```text
plan_id
lorry_id
created_by
created_at
status
total_boxes
total_volume
used_volume
remaining_volume
space_utilization
total_weight
remaining_weight_capacity
```

## 31.9 loading_plan_orders

```text
plan_id
order_id
```

## 31.10 box_placements

```text
placement_id
plan_id
order_id
box_profile_id
box_instance
x
y
z
placed_length
placed_width
placed_height
orientation
sequence_number
```

## 31.11 loading_reports

```text
report_id
plan_id
generated_by
generated_at
report_path
```

Report values should be derived from the saved plan rather than duplicated inconsistently.

---

# 32. Entity Relationship Summary

```text
User
├── Customer
├── Warehouse Administrator
├── Loading Supervisor
└── Seafood Supplier

Customer
   |
   | places
   v
SeafoodOrder
   |
   +---- OrderStatusHistory
   |
   +---- OrderItems

LoadingPlan
   |
   +---- LorryProfile
   |
   +---- SeafoodOrders
   |
   +---- BoxPlacements
            |
            +---- BoxProfile

LoadingPlan
   |
   +---- LoadingReport

LoadingPlan / LoadingReport
   |
   +---- LoadingAnalytics
```

Supabase PostgreSQL uses one `users` table with a `role` column.

---

# 33. Session State

Use `st.session_state` for temporary browser-session data only.

Recommended keys:

```python
st.session_state.logged_in
st.session_state.user_id
st.session_state.user_email
st.session_state.user_role
st.session_state.user_name
st.session_state.portal_mode
st.session_state.selected_order_id
st.session_state.selected_plan_id
```

Permanent data belongs in Supabase PostgreSQL.

---

# 34. Authorization Guards

Every protected page should verify authentication before rendering.

Concept:

```python
def require_login():
    if not st.session_state.get("logged_in"):
        st.stop()
```

Role guard:

```python
def require_role(*allowed_roles):
    role = st.session_state.get("user_role")

    if role not in allowed_roles:
        st.error("You are not authorized to access this page.")
        st.stop()
```

Do not rely only on hiding navigation buttons.

---

# 35. Status Design

Use consistent status badges.

Suggested visual categories:

- neutral → grey / blue-grey
- informational → blue
- success / active → teal / green
- waiting / warning → gold
- cancelled / failed → coral / red

Use exact status labels from project requirements.

---

# 36. Table Design

Staff pages should support:

- page title
- summary cards
- filters
- search
- sorting where useful
- status badge
- actions on right
- empty state
- destructive confirmation

Avoid over-wide tables.

On small screens hide non-critical columns or use expandable details.

---

# 37. Form Design

Follow Login/Register style.

Use clear labels.

Good:

```text
Lorry Internal Length (cm)
[ 450 ]
```

Use `st.number_input` for:

- dimensions
- weight
- quantity

Delete/cancel buttons should use warning/destructive styling and confirmation.

---

# 38. Dialog / Modal Design

Use dialogs or expandable panels for:

- Add Lorry
- Edit Lorry
- Delete Lorry confirmation
- Add Box Profile
- Edit Box Profile
- Cancel Order
- Update Status
- Order Details

Do not create a separate page for each small action.

---

# 39. Loading / Success / Error / Empty States

## Loading

Example:

`Generating optimized loading plan...`

## Success

Short and clear:

`Loading plan saved successfully.`

## Error

Explain the fix when possible.

Good:

`The selected lorry does not have enough weight capacity for these orders.`

## Empty

Example:

> No lorry profiles have been added yet.

Button:

`Add Lorry`

---

# 40. Responsive Design

## Desktop

Main target for Staff operations.

Use:

- custom sidebar
- wide tables
- multiple summary cards
- 3D view

## Tablet

Use:

- compact navigation
- two cards per row
- reduced table columns

## Mobile

Customer pages must remain usable.

Use:

- single column
- full-width controls
- smaller titles
- stacked buttons

Complex 3D planning can prioritize desktop/tablet.

---

# 41. Accessibility

Minimum:

- clear labels
- sufficient contrast
- do not use color alone for status
- readable buttons
- visible keyboard focus
- useful error messages
- alt text for images where possible
- avoid tiny essential text

---

# 42. Security Design

## Authentication

- hashed passwords
- unique email
- account status validation
- role validation

## Authorization

- Customer only accesses own orders
- Staff access depends on role
- protected pages have guards
- database operations verify permission

## Input validation

Validate:

- email
- phone
- quantities
- dimensions
- weight
- IDs
- statuses

## SQL

Always use parameterized SQL.

```python
cursor.execute(
    "SELECT * FROM users WHERE email = ?",
    (email,)
)
```

Never concatenate user input into SQL.

## Sensitive data

Never show:

- password hashes
- password salts
- secrets

---

# 43. Performance Targets

Where practical:

- normal UI actions: around 2 seconds
- 3D visualization: around 5 seconds
- loading plan generation: around 10 seconds

Use:

- preprocessing
- heuristic ordering
- optimized SQL queries
- solver time limits when needed

Show a progress/loading state during optimization.

---

# 44. Reliability / Data Integrity

Persist:

- users
- orders
- status history
- lorries
- boxes
- plans
- placements
- reports

Every saved loading plan must satisfy:

- valid coordinates
- no overlap
- inside lorry boundary
- weight constraint
- project stacking constraints

If no feasible plan exists:

- do not save it as valid
- show why generation failed

---

# 45. Reusable Components

## navigation.py

- Customer navigation
- Staff navigation
- Logout

## status_badges.py

- consistent status styling

## cards.py

- summary metric card
- action card
- empty state card

## tables.py

- standard table formatting

## dialogs.py

- confirmation
- edit dialogs

---

# 46. Customer Flow

```text
Homepage
   ↓
Order Seafood
   ↓
Not logged in?
   ├── Yes → Login
   │          ├── Existing → Login
   │          └── New → Register → Login
   │
   └── No
        ↓
Customer Dashboard
        ↓
Order Seafood
        ↓
Select Seafood
        ↓
Review Order
        ↓
Place Order
        ↓
My Orders
        ↓
Track Order Status
```

---

# 47. Staff Flow

```text
Homepage
   ↓
Staff Portal
   ↓
Staff Login
   ↓
Authenticate + Role Check
   ↓
Staff Dashboard
   │
   ├── Manage Customer Orders
   ├── Update Order Status
   ├── Manage Lorry Profiles
   ├── Manage Box Profiles
   ├── Generate Loading Plan
   │        ↓
   │   View 3D Loading Plan
   │        ↓
   │   Save Plan
   │        ↓
   │   Generate Report
   │
   └── Reports & Analytics
```

---

# 48. End-to-End Loading Workflow

```text
Customer places seafood order
        ↓
Warehouse Administrator reviews order
        ↓
Order confirmed according to approved workflow
        ↓
Eligible orders selected
        ↓
Lorry selected
        ↓
Box requirements loaded
        ↓
Optimization validation
        ↓
OR-Tools / optimization logic
        ↓
Valid loading plan
        ↓
Preview
        ↓
Regenerate if needed
        ↓
Save
        ↓
3D visualization
        ↓
Loading Supervisor follows sequence
        ↓
Loading/order status updated
        ↓
Report generated
        ↓
Supplier / authorized staff reviews analytics
```

---

# 49. Report Source-of-Truth Rule

Use:

```text
Saved LoadingPlan
      ↓
Saved BoxPlacement
      ↓
Report
      ↓
Analytics
```

Do not separately calculate report numbers using unrelated logic.

This prevents differences between:

- plan
- report
- analytics

---

# 50. Naming Conventions

## Files

Snake case:

- `customer_dashboard.py`
- `loading_visualization.py`

## Functions

- `authenticate_user()`
- `register_customer()`
- `generate_loading_plan()`

## Tables

- `users`
- `seafood_orders`
- `box_profiles`

## Session keys

- `user_role`
- `selected_plan_id`

## CSS

Prefer shared AquaLoad prefixes for reusable styles:

- `.aq-page-title`
- `.aq-card`
- `.aq-status-badge`

---

# 51. Error Handling

## Login

Handle:

- invalid credentials
- inactive account
- Customer using Staff Portal

## Registration

Handle:

- duplicate email
- invalid email
- invalid phone
- password under 8 characters
- mismatch

## Order

Handle:

- unavailable seafood
- invalid quantity
- order not editable

## Lorry

Handle:

- duplicate plate
- invalid dimensions
- inactive lorry

## Optimization

Handle:

- no selected order
- no lorry
- missing box data
- weight exceeds capacity
- infeasible placement
- solver timeout/failure

## Report

Handle:

- plan missing
- plan not saved
- invalid plan

---

# 52. Confirmation Rules

Require confirmation for:

- Cancel Order
- Delete Lorry
- Delete Box Profile
- Deactivate User
- Replace an existing saved plan
- Mark Order as Loaded when irreversible

Example:

> Delete lorry profile ABC 1234?

---

# 53. Data Filtering Rules

Customer pages always filter by authenticated `customer_id`.

Staff pages filter by role permission.

Never trust a user-provided ID without verifying access.

A Customer must not be able to view another Customer's order by manually changing an ID.

---

# 54. Logout

Logout should:

1. clear authentication session
2. clear selected order/plan state
3. return to Login or Homepage

Example keys to clear:

```python
[
    "logged_in",
    "user_id",
    "user_email",
    "user_role",
    "user_name",
    "selected_order_id",
    "selected_plan_id",
]
```

---

# 55. Recommended Implementation Order

## Phase 1 — Authentication integration

1. Keep Homepage
2. Keep Login
3. Keep Register
4. Make Login use Supabase PostgreSQL `users`
5. Add password hash verification
6. Seed/create authorized Staff accounts
7. Add real post-login routing

Do this before building many more pages.

## Phase 2 — Customer core

8. Customer Dashboard
9. Order Seafood
10. My Orders
11. Track Order
12. Profile / Change Password
13. Forgot / Reset Password

## Phase 3 — Staff management

14. Staff Dashboard
15. User Account Management
16. Customer Order Management
17. Order Status Management
18. Lorry Profile Management
19. Box Profile Management

## Phase 4 — Core FYP optimization

20. Space Optimization
21. Save Loading Plan
22. 3D Loading Visualization
23. Loading Sequence

## Phase 5 — Reporting

24. Generate Loading Report
25. Reports
26. Analytics
27. Download/export

---

# 56. Preservation Rules for Current Three Pages

Do not redesign Homepage, Login, or Register unless specifically requested.

Do not:

- change to unrelated colors
- introduce a different font family
- return Login/Register to split-screen layouts
- add demo/prototype labels
- expose test credentials
- add inner scrollbars
- add fixed-height iframe page rendering
- remove Customer / Staff separation
- allow public Staff registration

Allowed future changes:

- real routing
- Supabase PostgreSQL authentication integration
- success/error integration
- responsive fixes
- accessibility fixes
- security fixes
- small consistency improvements

---

# 57. New Page Acceptance Checklist

## Visual

- [ ] AquaLoad palette
- [ ] same typography
- [ ] clear title
- [ ] consistent spacing
- [ ] consistent radii
- [ ] obvious primary action
- [ ] no unnecessary text
- [ ] no prototype labels
- [ ] responsive

## Functional

- [ ] input validation
- [ ] success state
- [ ] error state
- [ ] empty state
- [ ] correct Supabase PostgreSQL read/write
- [ ] no fake data shown as real
- [ ] correct role permission
- [ ] navigation works

## Security

- [ ] login guard
- [ ] role guard
- [ ] parameterized SQL
- [ ] restricted data protected
- [ ] no plaintext passwords
- [ ] destructive action confirmation

## Data integrity

- [ ] IDs correct
- [ ] duplicates handled
- [ ] relationships remain consistent
- [ ] optimization validated before saving
- [ ] report matches saved plan

---

# 58. Final Design Direction

AquaLoad is **one product with two experiences**.

## Customer side

**Seafood first.**

The Customer should think:

> I can easily order seafood and understand the latest status of my order.

## Staff side

**Operations first.**

Staff should think:

> I can manage loading resources, generate a valid plan, understand the arrangement, and complete the loading workflow efficiently.

Recommended overall visual balance:

**80% modern seafood/logistics platform + 20% Malaysian coastal identity.**

This keeps AquaLoad professional without making it look like a tourism or government portal.

---

# 59. Core Functional Areas

AquaLoad contains eight main functional areas:

1. User Account Management
2. Customer Order Management
3. Order Status Tracking
4. Lorry Profile Management
5. Insulated Fish Storage Box Management
6. 3D Space Optimization
7. 3D Loading Visualization
8. Loading Report and Analytics

Overall workflow:

```text
Customer Account
      ↓
Seafood Order
      ↓
Order Confirmation / Status
      ↓
Lorry + Box Data
      ↓
Space Optimization
      ↓
Saved Loading Plan
      ↓
3D Visualization / Loading Sequence
      ↓
Loading Completion
      ↓
Report + Analytics
```

---

# 60. Developer Rules

1. Preserve the accepted Homepage, Login, and Register designs.
2. Use Streamlit as the primary web UI.
3. Use Supabase PostgreSQL for permanent application data.
4. Database role is the final authorization source.
5. `.aquaload` email naming is only a Staff convention.
6. Keep Customer UI simple.
7. Keep Staff UI operational.
8. Reuse components and styles.
9. Never show fake metrics as real.
10. Never show prototype/testing information in production UI.
11. Validate every database write.
12. Validate optimization results before saving.
13. Generate reports from saved plans.
14. Make 3D visualization use the same saved placement coordinates.
15. Keep one consistent AquaLoad design system across the whole application.


---

# 61. Latest Approved Functional Changes

## 61.1 Seafood Management and Stock Control

AquaLoad now includes a Staff **Seafood Management** function. Staff can add, edit, remove/unavailable seafood products, upload product images, manage availability status, view current stock, restock, deduct stock, set exact stock counts, and review stock movement history. Customer ordering shows the actual quantity currently available. The system prevents an order quantity from exceeding stock. Stock is reserved when an order is placed, adjusted when an eligible order is edited, and restored when an eligible order is cancelled.

## 61.2 Same Operational Functions for All Staff

Warehouse Administrator, Loading Supervisor, and Seafood Supplier titles may remain stored as job roles, but all three are treated as authorized Staff for functional access. All Staff can use Seafood Management, Customer Orders, Order Status, Lorry Profiles, Box Profiles, Space Optimization, 3D Loading Plan, Reports & Analytics, User Accounts, Profile, and Logout.

## 61.3 Appearance Preferences

Both Customer and Staff profiles include **Light**, **Dark**, and **System** appearance preferences. The saved preference is stored in `users.theme_preference`. System mode follows `prefers-color-scheme`. The theme applies to authenticated AquaLoad pages and is restored when the user signs in again.

## 61.4 Logout Visibility

The sidebar Logout button uses a white surface with dark navy text so the label remains clearly readable.

---

# 61. Latest Functional Refinements (Implemented)

The running codebase additionally follows `LATEST_REQUIREMENTS.md`, including Customer-location-based collection-point assignment, manual operational status progression, controlled seafood categories, standardized 35L/50L/75L/100L box templates and inventory, automatic kg-based box recommendation, shared Staff permissions, FastAPI REST-based lorry GPS tracking, improved Three.js loading visualization, and usefulness-focused Reports & Analytics.

---

# Latest UI Addendum — Payment and Appearance

AquaLoad includes an additional Customer checkout interface between Order Seafood and My Orders. The payment interface is for UI/FYP demonstration only and does not connect to Stripe or another real payment gateway. Customers can review seafood items, total seafood weight, unit prices, total amount, and choose Credit/Debit Card, Online Banking, or E-Wallet. Entered card/bank credentials are not stored. Completing the simulated checkout records a local AquaLoad payment reference, creates the Pending order, deducts stock, and continues the existing collection-point and order-status workflow.

The authenticated AquaLoad interface supports System, Light, and Dark appearance preferences. Light mode uses a bright white background and high-contrast navy text. Dark mode uses deep navy surfaces with high-contrast light text, muted text that remains readable, and explicitly styled inputs/placeholders/buttons/select controls. The Forgot Password public interface remains bright/light and does not display implementation notes at the bottom.
