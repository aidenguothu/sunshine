# Engineering model & data contract (SI only internally)

> This is an **independently developed preliminary screening model**, NOT a transcription or validation of ISO 10427-2 calculations or any competitor's proprietary mechanics. Licensed standards and qualified engineering review are required before claims of standards-conformant design or field predictive performance.

## A. Geometry and standoff (universal definitions)
Input: hole inside diameter `Dh` [m], casing outside diameter `Dc` [m], `Dh > Dc > 0`.
Nominal centered radial clearance `c=(Dh-Dc)/2` [m]. If casing center is offset radially by `e` [m], with `0 <= e <= c`, then the narrowest radial gap `g_min=c-e` [m] and **standoff ratio** `SOR=100*(g_min/c)` [%]. At e=0, SOR=100%; wall contact e=c => 0%. Clamp results to [0,100] ONLY after valid physical inputs; clamp must never hide malformed data.

For rigid centralizer with nominal effective OD `Dr` [m], if the rigid OD is the constraint that CONTACTS the wall and the axis is offset to maximum permitted eccentricity, `SOR_rigid_geometric = 100 * (Dr-Dc)/(Dh-Dc)` (%), bounded [0,100]. Requires `Dc <= Dr <= Dh`. **This is a geometric wall-contact estimate at a centralizer**; not an actual force/deflection prediction. A non-contacting rigid design can have different eccentricity. Below a rigid support, casing sag reduces standoff.

Example: Dc=177.8 mm, Dh=215.9 mm, Dr=205.0 mm => 71.3911% geometric wall-contact support SOR. If Dr > min restriction, block rigid product (unless verified special run-in design).

## B. Survey doglegs / graph
CSV required `MD,Inclination,Azimuth`; accepted aliases; mandatory explicit unit m/ft, degrees; normalized to metres and degrees. Check increasing MD, finite values, inclination 0..180, azimuth 0..360. Calculate dogleg angle `beta=acos(clamp(cos(I1)cos(I2)+sin(I1)sin(I2)cos(A2-A1), -1,+1))` [radians]. `DLS_deg_per_30m = beta_deg * 30/deltaMD_m`. Do not use azimuth delta alone; near vertical azimuth swings need not mean a big dogleg. Min curvature position integration is optional in R1 but should be implemented if 3D visualization is later introduced. Handle beta≈0 without divide by zero. Do not interpolate survey beyond data range without a visible warning.

## C. Buoyant weight (optional R1.1)
If actual tubular linear mass `m_kg_m` and steel density `rho_s_kg_m3` exist, `w_b = m*g*(1-rho_fluid/rho_s)` [N/m]. Default rho_s=7850 kg/m3 ONLY if user-visible and approved; fluid density must be supplied. This is a simplification: casing contents, tool joints, collars, multi-fluid conditions, friction and other loads may require more advanced treatment. If density/rho or mass unknown, no numeric force prediction.

For straight segments with inclination `I` from vertical, transverse distributed load from gravity ONLY: `q_perp = abs(w_b*sin(I))` [N/m]. This omits tension, curvature, actual casing contact, hole shape, fluid transitions and friction; never label it a full 3D side-load calculation. Show `curvature/tension not modeled` warning for deviated/dogleg wells. For material doglegs, suppress automatic engineering-grade SOR and route for review. User-configurable DLS risk warning level, not a presumed ISO limit.

## D. Simple sag screening (optional R1.1)
If casing ID `Di` and OD `Dc` and Young's modulus `E` supplied/approved, pipe area second moment `I_pipe = (pi/64)*(Dc^4-Di^4)` [m4]; stiffness `EI = E*I_pipe` [N m2]. For **straight, horizontal-ish, simply supported uniform transverse distributed load q and support spacing L**, textbook max beam deflection `delta = 5*q*L^4/(384*EI)` [m]. This ignores axial tension, continuous multi-span casing, non-linear wall contact, curved wellbore and support displacement, therefore is only a simplified sag-screening indicator. Check `EI>0, L>0, q>=0`. Zero-load => zero sag. Increase L => larger sag, very rapidly (L^4).

Illustrative midspan SOR when two adjacent supports have **already-established support SORs** and load is acting in consistent contact direction: `SOR_mid_screen = max(0, min(SOR_left,SOR_right) - 100*delta/c)`. Label `simplified midspan screening` with model assumptions. If support standoffs are unknown, midspan % must be unknown too. Do not compute a numeric SOR directly from casing OD, spacing and bow-spring SKU name alone.

## E. Bow-spring centralizer measured performance
The manufacturer should supply restoring-load vs standoff **pairs for each applicable casing OD/hole ID/test setup**, with revision, date and provenance. Load is in newtons, SOR a fraction 0..1. As side load rises, supported standoff generally decreases. Sort by `load_N`; reject duplicate loads, nonfinite points, out-of-range SOR or physically inconsistent curves (unless engineer explicitly approves an envelope). Piecewise-linear interpolation is a screening approximation between adjacent measured values; outside their envelope return `UNKNOWN` rather than extrapolating. The product's single `restoringForceAt67_N` value can be displayed for product comparison, but NOT used to fabricate an entire load curve.

For a straight, similar-load interval, preliminary support load approximation per centralizer: `F_side ≈ q_perp * (L_before+L_after)/2` [N], a tributary-length assumption. Use inverse curve (load->SOR) ONLY if correct SKU, hole diameter and approved measured data are present. This approximates bow compression under side load but excludes tension/curvature/casing continuity.

For support at a different hole diameter, do not reuse the curve silently: either use an explicitly approved hole-size interpolation scheme with tests or mark support SOR `UNKNOWN` and request tested/engineer-approved data.

Starting force, running force and restoring force are different product properties. They must never be interchanged. Without test-backed running characteristics, do not claim casing run feasibility or hookload.

## F. Placement and optimization
R1: use actual joints. Joint n position = defined joint-start MD + user-approved offset inside that joint. Fixed patterns every k joints (k=1,2,3) plus custom. Stop the pattern exactly at interval bounds; do not double-place at zone boundary; honor exclusions. Do not treat 'every k joints' as a fixed distance if actual joint lengths vary. Exact positions and BOM use joints as installed, not a geometric rough count.

R1.1: compute curves and sag for each span; default compare plans of k=1,2,3 with visual confidence/validity labels. **Optimization** may select the fewest units among *feasible* plans ONLY when reliable product curves are available, geometry/restriction constraints pass, interval modeling is inside validity range and all midspan SORs meet the customer target. Otherwise call it `pattern comparison`, not `optimized spacing`.

Higher-end optimizer deferred: candidate locations per actual joint, joint/interval constraints, mixed SKUs and constraints. Never claim global optimum with heuristic code.

## G. Restrictions and quality checks
- `Dc >= Dh` => impossible annular geometry, hard error.
- Rigid `Dr > minPassageID` => cannot pass, hard error (unless engineer explicitly verifies a different physical installation method).
- Bow free OD may be > hole ID, by design. Verify COMPRESSED OD and restriction running capability/test conditions; if test incomplete => `needs review`, not automatic failure.
- Hole washouts/oversized diameters reduce support and can invalidate curves; when no tested data for diameter, suppress prediction.
- Do not compute with negative fluid density, invalid casing ID, unapproved E, negative lengths, conflicting zones, duplicate joint positions, invalid MD outside well interval.
- Distinguish actual measured holes from nominal bit size; use caliper where available.
- Stop-collar `qtyPerCentralizer` comes from approved SKU/installation configuration, not a universal assumption of two. Include installation scheme in BOM.

## H. Units
Internal SI. In: `in * 0.0254 = m`; `ft * 0.3048=m`; `ppf (lbm/ft) * 0.45359237/0.3048=kg/m`; `ppg_US * 119.8264273=kg/m3`; `lbf * 4.4482216152605=N`; `psi * 6894.757293=Pa`. Never treat lbm as lbf. Outgoing chart labels change with unit mode; stored data does not.

## I. Calculation result quality/status
- `DIMENSIONAL_ONLY` — geometry, restrictions, placement, BOM; no force-based standoff.
- `SCREENING` — sufficient approved inputs + supported approximations; caveats required.
- `REVIEW_REQUIRED` — doglegs, data extrapolation, washouts, invalid curve or unknown dimensions; no 'meets target' claim.
- `SYNTHETIC_DEMO` — user loaded fictional/example SKUs or surveys; clear prominent banner.

## J. Don't misstate standard requirements
ISO 10427-1:2024 has bow-spring testing/performance scope (supplement to API Spec 10D seventh ed., 2021). ISO 10427-2:2004 concerns spacing and stop-collar tests; reaffirmed in 2025. This screening model is NOT certified to these standards. 67% standoff is NOT a minimum criterion automatically applicable to every well and should be editable from customer well program.
