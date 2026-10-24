# Sunshine Centralizer Placement and Casing Standoff Simulator

**UNVALIDATED PROTOTYPE — not for well design, operational placement, or standards
compliance decisions.** Includes prescribed-offset geometry and an ideal-support straight-beam spacing screen.
It does not predict real centralizer performance or optimize a full-string placement schedule.

## Quick start

From `/workspace/sunshine/simulator`:

```sh
python -m venv .venv
.venv/bin/python -m pip install --cache-dir /tmp/sunshine-pip-cache -e '.[dev,ui]'
.venv/bin/python -m pytest -q
.venv/bin/ruff check .
.venv/bin/streamlit run src/sunshine_sim/ui/app.py --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

Windows users can use `.venv\Scripts\python` instead of `.venv/bin/python`.
The UI accepts dimensions in mm; engine inputs are SI (m, kg/m, N, Pa).

## First calculation

```python
from sunshine_sim.engine.models import CasingSpec
from sunshine_sim.engine.standoff import single_joint_standoff

casing = CasingSpec(0.1778, 0.1571, 43.2, "N80", 12.0)
result = single_joint_standoff(casing, hole_diameter_m=0.2159, eccentricity_m=0.005)
print(result.standoff_percent)  # approximately 73.7533%
```

For circular sections, clearance c = (hole diameter - casing OD)/2; minimum gap
is c - e, where e is a prescribed center offset. Standoff = 100 (c - e)/c.
Assume constant offset over one straight joint. No sag, survey, tension, buoyancy,
centralizer force or fluid interaction is modeled. Impossible geometry raises an
error; it is never silently clipped. Grade/mass/ID/length are future solver inputs.

## Structure

```text
simulator/
  pyproject.toml
  src/sunshine_sim/
    engine/       # immutable models and geometric standoff function
    data/         # future validated catalog adapters
    ui/           # Streamlit prototype and cross-section visualization
    reporting/    # future traceable report generation
  examples/       # synthetic input only; no certified product claims
  tests/          # independent of Streamlit
  docs/ARCHITECTURE.md
../.github/workflows/simulator.yml
```

## Engineering plan, licensing and contributions

See [architecture, validation and roadmap](docs/ARCHITECTURE.md).
Use short feature branches and PR review; physics changes require engineering review.
Proprietary licensing recommended, subject to company approval. No open-source grant
is made here. No real Sunshine product catalog has been supplied or verified.
Dependencies use bounded compatible ranges, not a deployment lock; freeze and audit
an approved reproducible environment before beta/client releases.


## Version 0.2: ideal-support beam and spacing screen

Select **Ideal-support beam & spacing** in the UI. Start with the default 6 m span;
change inclination, internal/external fluid densities and casing dimensions. Try a
12 m span to see wall-contact rejection. Supply comma-separated spacing candidates;
the app reports the longest tested length meeting your illustrative target, or that
none pass. The 80% default is a demonstration target, not a regulatory requirement.

The engine uses a static simply supported Euler-Bernoulli beam with perfectly
centered end supports and uniform lateral effective weight:

```text
I = pi (OD^4 - ID^4) / 64
w = g (mass_per_length + rho_internal * A_internal - rho_external * A_outer)
q = w sin(inclination_from_vertical)
y(x) = q x (L^3 - 2 L x^2 + x^3) / (24 E I)
y_max = 5 q L^4 / (384 E I)
R_end = q L / 2
```

These are idealized closed-form beam relations, not an API/ISO placement method.
The minimum is evaluated analytically at midspan, independent of plot resolution.
If sag exceeds radial clearance, physical standoff is withheld because contact
requires a different solver. Deflections above 1% of span trigger an additional
prototype guard; this is not a validated operating-envelope criterion. Net upward
loading is unsupported and rejected. Support compliance, axial forces/end-pressure
effects, curved surveys, friction and continuous-string support interactions are
not modeled. A certified centralizer may perform worse than an ideal support.

The downloadable JSON records inputs, engine ID, assumptions, candidate results,
contact flags and unvalidated status. This is an engineering screening export, not
a signed design report. No product selection or mounting schedule is generated.

Regression coverage includes endpoints, symmetry, midpoint, equilibrium, vertical
and inclined loading, fourth-power span scaling, stiffness scaling, contact guards,
invalid inputs, infeasible candidates and both UI modes. These tests verify the
implemented ideal model; independent engineering/field validation remains required.

## Version 0.3: centralizer catalog and product comparisons

Select **Product catalog & comparison**. DEMO-A and DEMO-B are deliberately synthetic,
not Sunshine products or evidence of a sales claim. View their force–offset curves,
compare their standoff at identical conditions, and screen supplied isolated-span
lengths. Blank results mean unsupported/infeasible, not zero standoff.

### Enter a product

1. Expand **Enter / edit centralizer specifications**.
2. Use a new product ID to add an entry. Enter casing compatibility, free OD,
   curve test-hole diameter, starting/running forces, test reference and conditions.
3. Paste curve rows as `casing_offset_mm, net_lateral_restoring_force_N`, starting
   at `0,0`. Both coordinates must strictly increase after the first point.
4. Save to the session, select products to compare, and use matching casing/hole
   diameters. Download your catalog to retain edits; sessions are not a database.
5. Download the JSON report for complete inputs/provenance or CSV comparison for
   review. Neither export constitutes a qualified engineering recommendation.

A centralizer test laboratory/domain expert must confirm the curve interpretation:
this solver requires installed **net lateral restoring force versus casing-center
lateral offset**, for the stated hole, casing and documented loading branch/test
conditions. Individual bow compression or one restoring-force rating is insufficient.
The UI does not convert those measurements into a valid installed curve. Imports
and edits remain unverified; a certificate reference is not software certification.

### Mechanical assumptions

For an **isolated** straight span with two identical compliant end supports, each
reaction is `qL/2`. Piecewise-linear inversion of the installed curve gives support
settlement `e`. The span offset is `e + y_beam(x)`, with the analytic maximum at
midspan. Measured curve endpoints bound the calculation; force beyond the last
measurement is rejected. Floating-point endpoint tolerances are 1e-9 N (load) and
1e-12 m (test-clearance boundary), not engineering extrapolation allowances.

This ignores adjacent-span loading and continuous-string bending. In particular,
shared interior supports in a repeated string can carry approximately `qL`, not
`qL/2`. **Do not apply isolated-span candidate results as a full-string spacing
schedule.** Also excluded: nonlinear wall contact, well curvature, axial loads,
friction, coupling geometry, support rotation constraints and run-in simulation.
Starting/running forces and free OD are stored and displayed as metadata; they do
not prove run-in feasibility or change the installed lateral curve calculation.
Rigid/semi-rigid products, hysteresis branch mixing, net uplift and hole-size curve
rescaling are unsupported. Comparative results do not imply superiority in the field.

### Gate to operational use

Before engineer-approved job recommendations: supply reviewed company test data;
implement and validate multi-support string equilibrium/contact, survey geometry,
axial loading and mounting constraints; run independent blind benchmarks; establish
uncertainty/acceptance limits and sign off the operating envelope. A deadline or
passing software tests does not satisfy those gates. The present release is suitable
for supervised software evaluation and clearly labelled synthetic demonstrations.
