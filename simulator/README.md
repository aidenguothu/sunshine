# Sunshine Centralizer Placement and Casing Standoff Simulator

**UNVALIDATED PROTOTYPE — not for well design, operational placement, or standards
compliance decisions.** Current functionality is geometric screening with a supplied
casing offset; it does not predict centralizer performance or optimize placement.

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
