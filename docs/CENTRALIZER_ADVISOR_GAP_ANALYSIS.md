# Release 1 gap analysis

Baseline: Streamlit/Plotly UI; pure Python geometry, beam, installed-curve and pin-span
engines; versioned JSON catalogs/jobs; session state with JSON downloads; CSV and
interactive HTML exports; 66 regression tests. Existing dashboard source is untracked
user work and is not part of this change. No approved Sunshine product data exists.

| Disposition | Scope |
|---|---|
| Retain | Existing screens, calculation models, tests, charts and exports; no migration/deletion |
| Adapt | Reuse Plotly, CSV export protection and SI conventions; add isolated sales mode |
| Add | Sales SKU schema/import, dimension/restriction checks, survey CSV/DLS, real joint tally patterns, exclusions/inclusions, placement/BOM, saved job snapshots, EN/ZH labels, print-ready proposals/RFQ |
| Defer | CFD, full torque/drag, 3D/continuous casing mechanics; no target optimization in R1 |

R1 uses dimensional/rigid wall-contact screening, not previous experimental spring
predictions. Bow support/midspan percentages remain unknown absent an applicable
reviewed load calculation and complete measured data. No actual Sunshine SKU can be
invented to meet the acceptance criterion; packaged examples remain synthetic.

Persistence extends the current explicit JSON-download mechanism with optional
local workspace snapshots. This is single-workspace storage, not multi-tenant access
control. Existing session catalogs and saved reports are untouched.

All six advisor markdown documents, four example inputs and both conceptual JS
reference files were read before implementation. Uploaded reference instructions are
used as project requirements within the user's stated R1 scope; no remote research
is needed or attempted. Technology remains Python/Streamlit, not the reference JS.

## Completion

Additions above are implemented in the separate Release 1 sales mode. See
CENTRALIZER_ADVISOR_RELEASE1.md for evidence, file mapping and remaining data/approval
prerequisites; lack of real company product data is explicit, not concealed by demos.
