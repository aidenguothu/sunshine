# Scope and architecture

## Standards and engineering boundary

API Spec 10D and ISO 10427-1 address bow-spring centralizer specifications/testing;
ISO 10427-2 addresses centralizer placement and stop-collar testing. Confirm the
applicable API RP 10D-series documents, exact titles, editions, scope, and clauses
from licensed publications before implementing requirements. Do not confuse product
test acceptance with an approved full-string numerical solver. No licensed standard
was consulted or compliance demonstrated in this initial implementation.

The geometric identity implemented here is not an API/ISO placement method. A 67%
standoff value, for example, must not be treated as a universal operational acceptance
criterion. The engineering authority must set the target for each job. Standards
requirements, deviations, applicable product types, and test conditions need a
reviewed clause-to-requirement-to-test traceability matrix.

## Intended features (not yet implemented unless stated)

- Current: prescribed-offset, circular single-joint standoff and cross-section plot;
  immutable casing/centralizer data models, JSON screening export, unit tests.
- Current (v0.2): ideal centered-support, uniform-load straight beam; analytic
  midpoint minimum; supplied-candidate spacing screen; JSON screening export.
  This is not a product-qualified placement optimizer.
- Future: minimum-curvature survey interpolation; casing beam/contact equilibrium
  with buoyant loading, axial tension, inclination, curvature and centralizer support.
- Future: minimum and sampled standoff per joint and over the full string; include
  interior span minima, not just joint endpoints or centralizer locations.
- Future: constrained spacing/count/location optimization against job-specific
  standoff targets, permissible mounting points, product inventory and run-in limits.
  Establish feasibility first; report infeasible jobs explicitly. Recheck optimized
  schedules using the converged physical solver and refined spatial mesh.
- Future: measured-depth profiles, eccentric cross-sections, centralizer schedule,
  and reviewable PDF/CSV reports including assumptions, warnings and provenance.

## Input contract

All engine values use SI units; convert and label field units at import/UI boundaries.

| Group | Required for mechanical modeling |
|---|---|
| Geometry | Hole/caliper diameter versus measured depth, casing OD/ID, couplings, joint lengths, mass/length, grade and elastic properties; restrictions and shoe depth |
| Survey | MD, inclination, azimuth, units, north reference, datum, survey uncertainty; strict increasing MD and interval coverage |
| Products | Product/version/type, casing compatibility, free/compressed OD, measured restoring-force/compression curves, loading/unloading conditions, hole size, starting/running forces, test certificate/revision; mounting/stop-collar limits |
| Fluids | Internal/external density versus depth, temperature/pressure basis; rheology and flow only when modeling hydrodynamics/drag |
| Operating case | Landing/tension boundaries, run-in or static condition, friction assumptions, rotation/reciprocation if modeled, target standoff, allowable positions and placement constraints |

A single restoring-force number is insufficient for a nonlinear bow-spring model.
Starting and running forces constrain run-in feasibility; they are not interchangeable
with lateral restoring force. Rigid and bow-spring devices need different contact laws.
Do not extrapolate measured curves outside their validated range silently.

## Outputs

Per joint: MD start/end, sampled and minimum standoff ratio/percent, depth of minimum,
contact/invalid-state flags and model validity. Whole job: global minimum and depth,
centralizer product/count/MD/joint schedule, constraints/feasibility and uncertainties.
Reports retain input snapshot/hash, units, solver/catalog versions, convergence,
standards references/editions, deviations and engineering review status.

## Stack and module boundaries

Python 3.11+ with NumPy/SciPy for numerical work; Streamlit/Plotly for the internal MVP.
Use versioned JSON/CSV catalogs initially, then SQLite internally or PostgreSQL for
multi-user catalog/version control. The data adapter validates imports and constructs
immutable engine models. Never store confidential client job data in source control.

Engine modules expose pure typed functions and explicit result objects; no Streamlit,
HTTP, file access, mutable global catalog or implicit units in the engine. UI, batch
jobs and tests call the same engine. Reporting consumes saved inputs/results without
recomputing physics. Maintain independent benchmark fixtures outside UI code.

For client production use, prefer a React frontend + FastAPI service around the same
engine, with authentication, tenant isolation, authorization, job audit history,
secure storage/backups and versioned result schemas. Keep CPU-heavy solves in worker
jobs. Streamlit is an internal prototype, not a client security boundary by itself.

## Validation plan

1. Independently review geometric definitions and hand-check centered, contact,
   interference and dimensional/unit-conversion cases.
2. Validate future mechanics against analytic straight-span beam cases with explicit
   boundary conditions, force equilibrium, limiting cases and mesh convergence.
3. Obtain licensed applicable publications. A qualified engineer records exact
   editions/clauses and independently reproduces worked examples where available.
4. Load certified Sunshine bench force-deflection curves, hole/test configurations,
   hysteresis and repeatability; separate calibration cases from blind validation.
5. Compare approved company calculations and suitable independent software using
   identical inputs/assumptions; investigate differences, not just correlation.
6. Compare controlled test-well/field evidence and measurement uncertainties. A
   cement-quality log alone does not uniquely establish casing standoff.
7. Engineering authority sets documented acceptance tolerances before benchmarking.
   Archive golden cases, sensitivity bounds, solver residuals, and regression tests.

## Roadmap and release gates

- MVP: reviewed units/schemas, real catalog import, survey QA, straight-span mechanics,
  manual placement, standoff profile and draft report. Gate: analytic/bench benchmark
  agreement to pre-approved tolerances. Current skeleton precedes this milestone.
- Beta: deviated/curved contact solver, nonlinear support curves, uncertainty studies,
  constrained placement search, CSV/PDF outputs and controlled internal pilots.
  Gate: independent engineering review, blind validation, convergence and feasibility
  checks; no autonomous client recommendations.
- Production: validated operating envelope, requirements/standards traceability,
  signed engineering acceptance, access controls, audit/reproducibility, monitored
  releases, rollback and client training. Operational use requires authorized review.

## Repository and licensing

Keep the existing dashboard intact; simulator/ is a separate Python package in the
same repository. Use protected main and short feature branches (feat/, fix/, docs/),
PR checks and a domain-engineer reviewer for changes to physics or acceptance rules.
Tag releases and version the engine and catalogs separately. Do not push until the
repository's visibility and authorization to publish company material are confirmed.

Recommend proprietary licensing for the company engine, catalogs and client data;
company legal counsel should confirm ownership and approve the terms. No open-source
license has been granted by this skeleton. Add a counsel-approved LICENSE before
external distribution. Open source (e.g. Apache-2.0 or MIT) is an option only with
company authorization; exclude confidential catalogs/data and licensed standards text.
Third-party Python libraries retain their own licenses and distribution obligations.
