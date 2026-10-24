# Sunshine Centralizer Placement Advisor — Codex handoff

**Audience:** Codex implementing or improving an EXISTING centralizer simulator repository.  
**Business objective:** Help Sunshine Petroleum sell its OWN centralizers with trustworthy selection, indicative placement advice, professional sales-engineering reports, and RFQ handoff. This is NOT a full SLB/Halliburton/PVI clone.  
**Research reviewed:** public manufacturer and ISO sources (references in `04_COMPETITOR_RESEARCH.md`).  
**No external access required:** all required product requirements, formulas, examples, guardrails and tests are in this directory. Network proxy errors are not blockers.

## Start here
1. Put these files in a folder such as `docs/centralizer-advisor/` of the existing repository.
2. Ask Codex to read `01_CODEX_EXECUTION_PROMPT.md` first, then `02_PRODUCT_REQUIREMENTS.md`, `03_ENGINEERING_AND_DATA.md`, `04_COMPETITOR_RESEARCH.md`, `05_TEST_PLAN.md`.
3. Codex MUST inspect the repo before changing anything and preserve current stack, features, styling and persisted data.
4. Ask Codex to implement ONLY Release 1 and the compatibility/validation guards first. Do not implement complex 3D, CFD or fully coupled string mechanics.
5. Replace all fictional example SKUs and force curves with real Sunshine product/test data BEFORE presenting engineering numbers to customers.

## MVP scope
- Wizard: Job -> Hole & casing -> Sunshine product -> Placement -> Results -> Export/RFQ.
- Inputs: casing OD/ID or linear mass; hole diameters by interval; survey MD/inclination/azimuth CSV or simple profile; fluid density; joint length; analysis interval; user target standoff.
- Product library: manufacturer-approved SKUs, type, dimensional compatibility, rigid OD or measured bow-spring force-vs-standoff curve, stop collar rules, certificates/datasheets, availability.
- Options: fixed spacing (every 1/2/3 joints) and target standoff *only when supported by sufficient engineering data*.
- Outputs: editable centralizer installation list by joint/depth, graph by MD, constraints/warnings, bill of materials, non-binding RFQ, client-ready PDF via browser print/export or existing PDF library.
- Units: metric/field; internal SI; bilingual English/Chinese if app already supports it or easy to add.
- Store locally in existing database/localStorage; never require internet during calculation.

## Non-negotiable safety/integrity
- Mark calculations `Illustrative`, `Preliminary (simplified engineering model)`, or `Engineering review required`; NEVER `API-certified calculation`, `ISO-compliant placement` or `guaranteed cement isolation` without formal substantiation.
- ISO 10427-1:2024 is about bow-spring centralizer testing/performance; ISO 10427-2:2004 concerns placement calculations/stop collar tests. They do not make 67% a universal placement target.
- A single restoring-force-at-67%-standoff datapoint is NOT a complete load-deflection curve; do not fabricate continuous predictions from it.
- Real SKU names, dimensions, test data, price and certificates must come from authorized manufacturer inputs, never invented or scraped from competitors.
- If bow-spring force/standoff data missing, suppress calculated bow-spring standoff % and target-based auto optimization. Show product compatibility and 'data required' plus descriptive illustrations.
- Clearly distinguish 'at centralizer' and 'between centralizers'; minimum standoff is generally between centralizers for straight sections, but complex curvature requires specialist review.
- A rigid-centralizer *geometric wall-contact* standoff is not a prediction of actual downhole contact forces or cement displacement efficiency.

## Recommended release sequence
**R1 — Saleable demo:** Product matching; intervals and survey import; manual/fixed-joint placement; dimensional checks; geometric rigid centralizer estimate; basic bow test point display; charts; BOM; print-ready report/RFQ; honest modeling status.  
**R1.1 — Indicative engineering:** SI-unit pipe sag under uniform transverse load; buoyant weight; centralizer force-curve interpolation if actual measurements; conservative midspan screening; editable constraints, side-by-side scenarios. Independent validation required before customer use.  
**R2 (only if commercial demand):** Curvature/tension loading; stronger optimizer; detailed casing-running force; commercial integrations. No CFD/FEA/3D mud-displacement projects.

## Files
- `01_CODEX_EXECUTION_PROMPT.md` — paste as a Codex task
- `02_PRODUCT_REQUIREMENTS.md` — complete UI, data, logic and sales workflow
- `03_ENGINEERING_AND_DATA.md` — formulas, validity rules, API, test dataset
- `04_COMPETITOR_RESEARCH.md` — condensed offline research and URLs
- `05_TEST_PLAN.md` — verifiable acceptance cases
- `examples/` — DEMONSTRATION ONLY survey, product, force curve and job JSON
- `reference/screening_engine.mjs` and `reference/screening_engine.test.mjs` — zero-dependency Node reference mathematical utilities and tests
