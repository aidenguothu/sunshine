# Offline research summary and primary-source links
**Important:** This brief is based on publicly accessible references researched outside the Codex proxy. It is descriptive competitive intelligence, not a source-code/specification license. Do not implement proprietary internals or reproduce competitor visuals in Sunshine software.

| Vendor | Verified high-level features | What Sunshine should adopt | Avoid in MVP |
|---|---|---|---|
| PVI CentraDesign | Specify spacing, location, target standoff, optimum; bow/rigid/semi-rigid/molded; standoff/torque-drag comparisons | User-driven pattern comparison, support/midspan profiles, specific joints | Complex 3D mechanics/torque-drag engine |
| Weatherford CentraPro Plus | Fixed spacing/fixed standoff; measured centralizer performance by casing/hole combination; support reaction and casing sag; reports & stop-collar quantities | Approved SKU/test library, staged pre-sales reports, data traceability | Proprietary force equations and detailed drag modeling |
| Halliburton Landmark WELLPLAN / historical OptiCem | Centralization placement in broader well-engineering suite; required standoff or fixed spacing (historical release); casing running context | Survey and interval workflows | Integrated well engineering enterprise stack |
| Halliburton iCem | Standoff profiles/soft-or-stiff string centralization embedded in hydraulic/cement displacement | Explain why standoff matters for cementing | Full hydraulic or CFD displacement simulation |
| SLB CEMENTICS | Centralization and mud-removal workflows, 3D-aperture mud displacement | Technical narrative tying product to cementing process | Large multiphysics simulation |

**PVI HTML case study (strongest short inspiration)**: fixed one-per-joint vs two-per-joint; compare min standoff at centralizer vs span; optimizing quantity subject to standoff target. The page uses a historical case study; figures are NOT general recommendations. https://www.pvisoftware.com/blog/casing-centralizer-series-4-case-study/

**PVI brochure:** four placement modes and product types. The PDF may not be accessible in some proxy networks; HTML case study above is safer: https://www.pvisoftware.com/brochure/English/CentraDesign-Centralizer_Placement_Model.pdf

**Weatherford current VariForm product page:** publicly describes CentraPro Plus predicting standoff, running force/hookload, spacing, sag, and choosing designs. https://www.weatherford.com/well-construction-and-completions/cementing/centralizers/variable-design-centralizers/

**Weatherford CentraPro Plus historical brochure (copyright 2002–2007):** explicitly explains per-pipe/hole test data, 3D force analysis, 'fixed standoff' and 'fixed spacing', sections, stop collars, reports. Do not assume every historic feature/version reflects the latest installation. https://www.weatherford.com/documents/brochure/products-and-services/drilling/centrapro-plus-centralizer-placement-system/

**Halliburton WELLPLAN current page:** https://www.halliburton.com/en/products/engineers-desktop-suite/wellplan-software

**Halliburton iCem current page:** https://www.halliburton.com/en/products/icem-service

**SLB CEMENTICS:** https://www.slb.com/products-and-services/innovating-in-oil-and-gas/well-construction/well-cementing/cement-software/cementics-zonal-isolation-software

**SLB centralization within mud removal:** https://www.slb.com/products-and-services/innovating-in-oil-and-gas/well-construction/well-cementing/mud-removal

**ISO 10427-1:2024 official:** bow-spring centralizer performance/testing/marking; not necessarily applicable to rigid centralizers. https://www.iso.org/standard/86807.html

**ISO 10427-2:2004 official:** placement calculations and stop-collar testing; 2025 reaffirmation. https://www.iso.org/standard/32501.html

**Minimum curvature background:** https://pubs.usgs.gov/wri/1983/4275/report.pdf

## Competitive messaging recommendation
Customer-facing wording: `We help you select suitable Sunshine centralizers and prepare a preliminary centralizer placement proposal based on your well geometry and the product data provided.`

Not acceptable: `Our simulation predicts exact zonal isolation/guarantees 70% downhole standoff/duplicates SLB and Weatherford physics/is ISO 10427-2 certified.`

## Product information Sunshine MUST gather internally
For each actual SKU: part number/series, photo, OD/casing/hole fit, compressed OD/restriction clearance, bow force-deflection curves measured at the relevant hole IDs, starting/running force reports, stop collar configuration/holding force, installation instructions, material/temp limits, product datasheet version, certification/test provenance, commercial status and authorized net pricing (private). Without these, there is no trustworthy numerical manufacturer-specific comparison.
