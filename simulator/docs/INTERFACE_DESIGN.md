# Interface review and design decisions — 2026-10-24

## Online review boundary

Attempted HTTPS access to the public SLB, Halliburton, Landmark Solutions,
Weatherford, Pegasus Vertex and Bing search websites. All six returned proxy
403 tunnel errors. No vendor screenshots, current feature lists, or proprietary
algorithms were retrieved. A comprehensive online competitive review therefore
remains incomplete; this implementation is an independent design, not a claim of
commercial feature parity. Previously discussed vendor product names are not
verified references for the new diagrams.

## Implemented design

- Separate job geometry, placement editing, results inspection and candidate search.
- Align depth tracks vertically, with measured depth increasing downward; no false
  TVD or 3D trajectory representation of the straight-interval model.
- Two-track centered design preview, four-track calculated result workspace.
- Explicit casing OD/bore, caliper envelope, product-colored placement markers and
  stylized bow glyphs. Transverse/depth scales are independent and labelled.
- Keep local standoff profiles separate from conservative bound traces; distinguish
  target shading from unsupported-span shading, which also has status-table text.
- Show support reactions in kN and input diameters in mm on result plots, while
  retaining SI input tables. No change to calculation units.
- Select MD for a linked horizontal reference and circular section inspection.
  This is explicit input selection, not click-to-place or drag-to-place editing.
- No interpolation through unsupported spans. Cross-section predictions are withheld
  there. A centered design preview is explicitly different from calculated geometry.
- Review tables and JSON/CSV exports remain available; standalone HTML supports
  interactive diagram sharing without requiring the application server.

## Verification

Automated checks cover depth direction/alignment, mm and kN conversion, true section
aspect ratio, low-side gap consistency, design/result separation and unsupported
geometry withholding. Real Chromium navigation checks the results/section tabs and
absence of Streamlit exceptions. Visual inspection corrected track-heading overlap.
Engineering validation status remains unchanged.

## Remaining UX / engineering work

Drag placement, linked hover between tracks, full well trajectory display, field-unit
input switching, authenticated saved projects, before/after scenario overlays and
reviewed printable engineering reports are not implemented. Production simulation
still requires the mechanics and validation gates in ARCHITECTURE.md.
