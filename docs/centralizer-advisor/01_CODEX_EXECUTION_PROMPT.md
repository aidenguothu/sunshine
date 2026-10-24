# CODEx TASK — INTEGRATE INTO MY EXISTING CENTRALIZER SIMULATOR

You are working INSIDE my current project repository. You cannot depend on external browsing: SLB, Halliburton, Landmark, Weatherford, PVI and generic search have returned network-proxy errors. Do not retry remote endpoints or halt for those errors. I have already supplied the research in this directory.

GOAL: Adapt my existing app into a polished **Sunshine Centralizer Placement Advisor** that helps our sales team select and sell Sunshine centralizers. Avoid a sophisticated well-construction/CFD/FEA application. Preserve existing working functionality and avoid a wholesale rewrite.

READ FIRST: `00_READ_ME_FIRST.md`, `02_PRODUCT_REQUIREMENTS.md`, `03_ENGINEERING_AND_DATA.md`, `04_COMPETITOR_RESEARCH.md`, `05_TEST_PLAN.md` and available example inputs. The reference JS engine is conceptual, not a mandate to replace the app's current technology.

YOUR WORK ORDER:
1. Inventory repo (framework, routing, current calculation engine, charts, document export, tests, state/storage, existing catalog). Write a brief gap analysis IN THE REPO as `docs/CENTRALIZER_ADVISOR_GAP_ANALYSIS.md` listing retain/adapt/add/defer, distinguishing existing functionality from planned changes.
2. Add or repair product master schema. Use manufacturer-approved actual data if already present, otherwise load `examples/` as conspicuously tagged DEMO data. No fictitious real product certificates, pricing or engineering performance.
3. Make a 5-step flow: Well/job; Casing/hole/survey; SKU compatibility; Placement choices; Results/report/RFQ. Maintain accessible responsive design; use existing UI framework and chart/PDF components where possible.
4. Engineering R1: normalize all calculations to SI; validate OD < hole ID; support joint-indexed placements; plot centralizers vs measured depth and incline; show clear at-centralizer vs between-centralizer descriptions. For rigid products, wall-contact geometric standoff may be displayed as a bounded screening figure; for bow-spring products without COMPLETE measured curves show "standoff not calculable from available test data". Implement no undocumented physics as definitive results.
5. If time and repo architecture allow, add optional R1.1 'Indicative sag screening': `03_ENGINEERING_AND_DATA.md`; self-contained pure functions with tests. Require measured force curves for credible bow-spring support estimates; otherwise NO predicted numeric standoff based on an invented spring constant.
6. Fixed spacing modes: every joint, every 2 joints, every 3 joints; custom joint selection; force inclusion/exclusion intervals; beginning/end placement offsets. Output installation instructions (joint number and MD) without physical impossibilities. Target-standoff optimization must remain disabled or "experimental / reviewer approval required" until the calculation model is validated and support data available.
7. Customer output: 2–3 page print/PDF engineering SALES PROPOSAL with well inputs, specific actual SKU(s), methodology badge/text, standoff visual only when calculated, placement schedule, BOM, disclaimer, account manager contact and 'Request Quote' CTA. Prices only if company inputs them; never invent. Admin can export BOM CSV.
8. Add bilingual EN/ZH terminology where practical. Preserve data across reload with existing storage mechanism. No mandatory server or external SaaS to run the MVP.
9. Add and RUN regression + calculation tests. Output a test results summary and list of model limitations. Do not call simulated data validated test data.
10. Give me a final changelog with changed files and exact commands to run locally. If dependencies are missing offline, use what already exists or implement browser-native alternatives; don't waste time trying to download competitor documents.

CONSTRAINTS:
- Preserve current repository structure, code style, components and tools wherever reasonable.
- No reliance on external network for data, calculations or previews.
- Do not remove customer data or existing reports without a migration.
- No marketing claims of guaranteed zonal isolation, fully ISO/API compliant placement, precise torque-and-drag or exact 3D mechanics.
- All defaults (diameters, weights, unit conversions, selected target) must be explicit, labeled and editable; DO NOT silently invent customer well data.
- All demo products carry the message "SYNTHETIC EXAMPLE — REPLACE BEFORE CUSTOMER USE".
- If conflicting requirements arise, prioritize physical consistency and transparency over attractive but unsupported numbers.

ACCEPTANCE CRITERIA:
- I can select a valid real Sunshine SKU, create/load a well, specify a placement interval and select every-1/2/3-joint placement without internet.
- I can load a CSV with MD, inclination, azimuth (and optional hole-size interval CSV) and get appropriate errors for bad data.
- I can see exact positions/counts, a clear cross-section/standoff explanation, a measured-depth placement profile and a print-ready proposal.
- With no restoring-force curve, no bow-spring standoff percentage is displayed as an engineering fact.
- Ineligible SKU/diameter/restriction combinations are blocked or explicitly require engineering review.
- Tests in `05_TEST_PLAN.md` pass. Existing tests still pass.

FIRST RESPONSE TO ME: succinctly describe your existing-repo findings and intended small changes; then IMPLEMENT rather than rewriting or asking permission for routine choices.
