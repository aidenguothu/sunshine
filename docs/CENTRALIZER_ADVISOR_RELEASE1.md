# Release 1 implementation and validation

## Basis and scope

Read 01_CODEX_EXECUTION_PROMPT.md first, then every other Markdown document in
centralizer-advisor/, all supplied examples and both reference JS files. These are
user-supplied project requirements/research, not instructions to replace the existing
stack. No online searches or competitor endpoint requests were made during this task.

## Retained

Python/NumPy/SciPy pure engines, Streamlit/Plotly UI, existing four calculation modes,
model assumptions, versioned demo files and existing exports remain. All 66 baseline
tests remain in the suite. No pre-existing dashboard files, customer files or reports
were removed. No CFD, full torque-and-drag, 3D or continuous-string solver was added.

## Changed files / responsibilities

- `docs/centralizer-advisor/`: all 12 uploaded files, preserved as local requirements,
  research, examples and conceptual reference utilities.
- `docs/CENTRALIZER_ADVISOR_GAP_ANALYSIS.md`: initial retain/adapt/add/defer inventory.
- `simulator/src/sunshine_sim/advisor/engineering.py`: SI conversion, strict survey/
  hole CSV import, spherical dogleg, pure reference screening helpers.
- `advisor/catalog.py`: separate sales SKU schema, dimension/evidence/collar/price
  metadata, demo identity guards, JSON/CSV adapters.
- `advisor/placement.py`: actual joint tally, fixed/custom patterns, legal offsets,
  include/exclude zones, body/connection/exclusion overlap checks where dimensions exist.
- `advisor/service.py`: dimensional eligibility, passage checks, rigid geometric SOR,
  explicitly unknown bow/between-support SOR, mixed-SKU assignments and BOM aggregation.
- `advisor/storage.py`: versioned job/catalog bundles, explicit atomic local saves,
  name/path guards and schema validation.
- `advisor/proposal.py`: escaped, offline print-ready HTML; model/revision/UTC/evidence,
  installation schedule, BOM, disclaimer, consent-selected contact data and unsent RFQ.
- `ui/sales_screen.py`: additive five-step EN/ZH sales flow, SI/field boundary conversion,
  charts, snapshots, exports and proposal controls. Stable editor baselines avoid
  applying added/deleted-row patches repeatedly during reruns.
- `ui/app.py`: new sales mode, existing modes preserved and explicitly experimental.
- `data/examples/sales_job.json`, `sales_catalog.json`: mappings of supplied synthetic
  fixtures, not invented manufacturer product data.
- `tests/test_advisor.py`, `tests/test_ui.py`: numerical, input, persistence, mixed BOM,
  proposal safety, units and UI regression coverage.
- `.gitignore`, `pyproject.toml`, `README.md`: ignore workspace saves; v0.6 metadata;
  operating/data-import/report instructions. No new dependencies.

## Validation evidence

- Python suite: **94 passed**, including all 66 pre-existing tests.
- Ruff: all checks passed.
- Supplied Node reference: **7 passed**, zero failures/skips.
- Streamlit tests: 1/2/3/custom patterns, equivalent metric/field results, missing bow
  SOR, invalid custom input, mixed SKU BOM and stable dynamic tally edits.
- Chromium browser: five-step navigation, joint-pattern change, proposal download,
  explicit workspace save and reload/open restore of the 17-unit pattern. Network
  interception allowed loopback only; there were no required external requests.
- Offline proposal print: rigid and bow examples produced three-page A4 PDFs. A
  rendered PDF page was visually inspected for BOM, review warnings, disclaimer,
  account-manager section and RFQ. Synthetic warnings appear on every proposal page.
- Reference test cases cover geometry limits, 71.391% rigid example, beam scaling,
  unknown one-point/out-of-envelope curves, survey wrap/limits/duplicate MD, exact
  hole-section boundaries, restriction failures, bow free-vs-compressed checks,
  actual variable joint lengths, per-SKU collar rules, save/load and demo identity.

## Acceptance boundaries and remaining prerequisites

No authorized actual Sunshine SKU/test certificate/datasheet/price was supplied.
Therefore actual-product customer-use acceptance cannot be asserted; the workflow
accepts company-provided sales-1 metadata but bundled products remain conspicuously
synthetic. Missing body/bore/collar references are not fabricated; they require review.

R1 does not predict bow support or between-support standoff or prove field outcomes.
Force-curve interpolation helpers exist with tests, but are not used to infer loads
in the R1 proposal. Material doglegs/incomplete survey trigger review; survey angles
are shown without extrapolating force results. A rigid number is strictly a bounded
wall-contact geometric estimate at the product, not a cement-displacement prediction.
No target optimizer or meets-target claim exists in this mode.

Workspace persistence and catalog upload have no login/tenant/approval security.
Use in a controlled internal workspace. Portable files may contain customer data.
Contact consent controls export only, not an external transmission; no RFQ is sent.
Role-based approval, authenticated client sharing and advanced mechanics remain
separate future work. Licensed standards and responsible engineer review remain
necessary for standards or operational claims. User-supplied research summaries
inform this design; no proprietary algorithms/visuals are copied.
