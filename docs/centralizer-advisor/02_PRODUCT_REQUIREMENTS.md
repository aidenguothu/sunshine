# Product requirements — Sunshine Centralizer Placement Advisor

## 1. Positioning, users and value
**Purpose:** Lead generation and technical pre-sales. NOT a directional drilling, hydraulics, torque/drag or cement-displacement simulator.

**Primary users:** operator cementing engineers, service-company field engineers, distributor sales engineers, Sunshine sales staff.  
**Success metrics:** time to create an RFQ, completion rate, validated product shortlist, report downloads, qualified enquiries, percentage of submitted reports with fully traceable product test data.

## 2. Essential screens (desktop-first, mobile-friendly)
**Screen A — Create job**
Customer/project/well ID (optional for demo); region; casing string/interval top & bottom measured depth; unit system (m/in, kg/m/ppf, kg/m3/ppg); engineering grade (Demo / Preliminary). No contact capture until explicit report/RFQ action.

**Screen B — Geometry and trajectory**
Casing OD and ID or verified casing unit weight (manual user selection rather than guessed dimensions); joint length and physical joint-count if known; hole ID / caliper profile by depth; previous casing ID / minimum restriction; mud/cement density and mode; survey CSV `MD,Inclination,Azimuth`; optional manually-defined profile (vertical/build/hold/horizontal), tagged synthetic. Plot inclination and dogleg severity vs MD.

**Screen C — Sunshine centralizer product**
SKU and photo/outline; family (bow spring, rigid, semi-rigid, molded-on); intended casing OD and hole/restriction ranges; maximum outside diameter (free/compressed or rigid), min ID, centralizer length; bow restoring-force dataset and test condition if available; starting force and running force separately; stop collar type/count, test report source and revision, permissible installation positions, certification status. Show `Suitable / Not Suitable / Verify` for dimensions. Never use unapproved supplier data.

**Screen D — Placement**
Three tabs: Fixed pattern (one every 1, 2, or 3 joints), Custom placement (toggle individual joints or paste list), Compare options (side by side). Allow zone-specific target standoff (CUSTOMER-SPECIFIED, not hardcoded 67%). Allow edit at exact MD restricted to physically allowed joints/intervals. Settings: start/end offsets, joint length, no-go zones, selected product per interval, high-priority cemented zones. Explicit check if installation on connections/couplings or where stop collars cannot fit.

**Screen E — Results & export**
KPI cards: centralizer units; stop collars/retainers by SKU rule; nominal spacing; screened standoff (ONLY if supported); failed constraints; estimated hardware quantity/cost (ONLY if provided). Interactive charts: inclination + placement tick marks by MD; user target + centralizer/endpoints/midspan profile where computed; danger intervals. Bottom: installation schedule (`joint_no`, `MD`, `SKU`, `stop_collar_qty`), BOM, methodology/warnings. Buttons: change scenario, download installation CSV, print/save PDF, email/copy RFQ text without sending automatically.

## 3. Commercial workflow
- SKU-first entry: customer chooses one of our products and learns fit/benefits.
- Job-first entry: customer uploads survey; app shortlists fitting actual products.
- Comparisons: "economy / balanced / high coverage" **scenarios** based on user-selected every-3 / every-2 / every-1 joint placements, NOT marketing claims of equal field performance.
- Suggested upsell must be justified by constraints/test-backed performance; do not maximize product counts at the expense of credibility.
- RFQ fields: contact name, company, country, email (optional until voluntarily submitted), well/job reference, SKU, quantities, drawing/revision, desired Incoterms, required delivery date, notes. Data privacy/consent explicit. No backend email integration for MVP unless already present and approved.
- Report: branding, source data and revision, assumption summary, result validity level, product image + actual datasheet link (if user-provided), recommended quantities, install locations, optional quote references, disclaimer.

## 4. Requirements by priority
### P0 — must ship
- All dimensional checks; survey CSV import; basic charts; editable placements; SKU library and admin upload; SI conversions; saved jobs/scenarios; BOM; printable proposal; quality flags + validation; no internet dependency.
- Store underlying inputs/results as versioned JSON; report includes model version and UTC timestamp.
- Validate every survey MD strictly increasing; inclination 0–180°, azimuth 0–360°, handle 360° wrap; tie survey interval to placement interval and warn on extrapolation.
- Verify not assigning a centralizer to an interval with hole ID <= casing OD.
### P1 — useful, manageable
- Estimate minimum geometric clearance and rigid-contact SOR.
- Optional load-curve-backed bow support estimate and sag screening using separately documented simplified beam model.
- SOR overlay at support and midspan, with qualification "screening / review required".
- Compare three placement plans by count + data quality + result; manual override.
### P2 — defer
- Full torque & drag, non-linear 3D casing mechanics, multi-phase fluid rheology, CFD, FEA, cloud CRM, login, pricing API, custom 3D animation, real-time telemetry and sophisticated optimizer.

## 5. UX details that drive credibility
- Every numeric value shows unit and origin: `customer supplied`, `manufacturer test`, `user assumption`, `software approximation`, `synthetic demo`.
- Use cross-section illustration showing hole/casing/annular gap; a simple SVG is sufficient.
- Give contextual explanations: e.g., "Your 7-in casing has 0.75-in nominal radial clearance in an 8.5-in hole. Actual center offset and contact determine standoff."
- Tooltip on percentage: "SOR = closest casing-to-hole gap / nominal centered radial clearance".
- Report never calls a simplified screening result "precise" or "field proven".
- Do not use competitors' branding, screenshots, code or proprietary algorithms in the product.

## 6. Internal data model (conceptual — map onto existing app types)
```
Job { id, version, customer, wellName, mode, units, intervalTopMD_m, intervalBottomMD_m,
      casing: {od_m, id_m?, massPerLength_kg_m?, modulus_Pa?},
      fluids: [{topMD_m,bottomMD_m,density_kg_m3,phase}],
      holeSections: [{topMD_m,bottomMD_m,holeID_m,restrictionID_m?,source}],
      survey: [{md_m,inclination_deg,azimuth_deg}],
      joints: {length_m, startMD_m, allowedPositionsWithinJoint_m[]},
      targets: [{topMD_m,bottomMD_m,targetStandoff_fraction}],
      placement: [{md_m,jointIndex,sku,retainerQty,locked}],
      metadata: {revision, createdAt, modelVersion} }
SKU { sku, manufacturer, family, casingODRange_m, holeIDRange_m,
      freeOD_m?, compressedOD_m?, rigidOD_m?, minPassageID_m?, length_m,
      loadCurveByHoleSize?: [{holeID_m, testRevision, points: [{load_N, standoff_fraction}]}],
      restoringForceAt67_N?, startingForce_N?, runningForce_N?,
      retainerQtyPerUnit, datasheetReference?, evidenceType, approvedForCustomers }
Result { validity: 'demo'|'screening'|'engineering-review', reasons[], constraints[],
         placement[], depthProfiles[], billOfMaterials[], costIfConfigured?, units, modelVersion }
```
Unit conversions at boundaries only; DO NOT mix lbm, lbf, kgf, kg, N.

## 7. Technical implementation
- **Best case:** extend existing React/Vue/other app, TS/JS, existing charting and reporting packages.
- **Fallback:** browser-only SPA; offline bundling; built-in SVG charts and `window.print()` with print CSS. A native file download can save JSON/CSV. No compulsory database or network calls.
- Separate modules: `catalog/`, `surveys/`, `engineering/`, `placement/`, `reporting/`, `i18n/`, `validation/` (adjust actual layout to repo).
- Pure deterministic calculation functions, serializable job state, testable outputs. Never blend physics, UI, formatting and RFQ side effects into one function.
- Admin versus user edit permissions may be handled simply (read-only approved catalog loaded from bundled JSON) until authentication is justified.

## 8. Client-facing disclaimer (use exact intent, editable by company counsel)
"This preliminary centralizer placement assessment is based on supplied well data and a simplified screening model. It is intended for product selection and quotation support, not as a substitute for detailed well-engineering, casing-running or cementing design. Final centralizer type, spacing, stop-collar selection and placement must be verified by the responsible qualified engineer against actual well conditions, current standards, and manufacturer test data. No cement isolation or run-to-bottom performance is guaranteed."
