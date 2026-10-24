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

## Version 0.4: job placement planner

Select **Job placement planner**. A complete synthetic job is loaded automatically:
1000–1024 m MD, two 7-inch casing sections with different weights/IDs, 60-degree
inclination, caliper washouts, and nine DEMO-B centralizers at 3 m spacing.

1. Inspect/edit casing rows, survey and caliper tables. Table units are SI: m, kg/m,
   Pa and degrees. This screen deliberately labels diameters in m, not mm.
2. Edit each placement's MD and select its product. Use **Generate placement rows**
   for a starting layout; end supports and casing-section boundaries are included.
3. Click **Run current placement** for the profile, support reactions/offsets,
   conservative per-span/per-joint bounds and a downloadable schedule/report.
4. Try DEMO-A on one support and rerun; adjacent-span predictions change.
5. Click **Compare regular layouts for all catalog products** to evaluate supplied
   nominal spacings and report the fewest supports among tested passing layouts.
   This bounded search does not optimize arbitrary mixed-product schedules or cost.
6. Download editable job JSON and catalog JSON separately to preserve your inputs.
   Load the catalog before importing a job using its product IDs. Report JSON includes
   the full catalog snapshot and input job; editable job JSON is a separate format.

### Model limits

Spans share support forces (interior reaction = sum of neighboring half-span loads),
while each span is assumed pin-connected. Linear end-settlement plus beam sag gives
its offset. This is **not** a continuous elastic casing string: rotations need not be
continuous, and bending moments across supports are omitted. Curved surveys, varying
OD across casing sections, contact, friction and axial tension remain unsupported.
Survey and caliper must cover the entire interval; every casing-section boundary
must have a support. Casing-section joints restart at the section start, and the
last joint may be partial. This isn't a measured tally import yet.

Caliper is interpolated linearly, including washouts between supports. Each support
requires a matching test-hole curve; no rescaling is performed. The minimum radial
clearance and analytic maximum offset yield a **conservative standoff lower bound**.
The actual minimum ratio and its depth can differ; the reported maximum-offset MD
is not presented as minimum-standoff MD. Profile points illustrate local predictions.
If the bound permits contact, results are withheld pending a contact solver rather
than reporting a negative physical standoff. Per-joint bounds use overlapping span
envelopes and can be conservative further. No operational approval is implied.

### Commercial workflow reference

This UI follows the requested general workflow: job geometry → product catalog →
manual placement → simulate → compare layouts → export. Attempts to retrieve public
SLB and Halliburton pages on 2026-10-24 were blocked by the environment's network
proxy (403). Their current feature sets, algorithms and numerical equivalence have
**not** been verified. No proprietary implementation or standards-compliance claim
is made. A future product review should use accessible official documentation and
licensed benchmark cases; visual workflow similarity is not engineering validation.

## Version 0.5: depth-aligned design and results workspace

The planner now separates **Well design**, **Centralizer placement**, **Simulation
results**, and **Layout comparison** into tabs. Design/placement previews show the
centered casing and caliper; they are not simulation predictions.

After running, inspect four shared-MD tracks: local well schematic, hole/casing
sizes, standoff with conservative bounds/target, and support loads. Depth increases
downward. Product colors remain consistent across placement symbols and loads.
Stylized bows mark centralizer positions; glyph length is exaggerated and does not
represent product dimensions. The schematic uses independently scaled transverse
and depth axes and is not a trajectory/TVD plot.

Use **Inspect measured depth** and the **Cross-section inspector** to view the local
hole, casing OD/ID, interpolated standoff and low-side gap. The circular view uses
equal aspect ratio. Unsupported spans are highlighted, their casing prediction is
omitted, and their cross-section is withheld. Sampled local values and conservative
span/joint bounds remain explicitly separate.

**Download interactive diagram (HTML)** produces a self-contained Plotly diagram
that can be opened offline. It retains the unvalidated/demo notice. It contains the
job visualization, so treat it as confidential when using company/client inputs.
The existing JSON reports and CSV schedules remain available.

UI validation included a real Chromium browser run and visual inspection of the
results and section screens, in addition to automated axis/unit/invalid-span tests.
No calculation-engine changes or additional engineering validation are implied.
