# Test and acceptance plan

Use unit tests for pure numerical functions, data validation tests for CSV import, browser UI tests where existing infrastructure exists and at least one review of print output.

## Deterministic math tests
1. `c=(Dh-Dc)/2`: Dh=0.2159 m, Dc=0.1778 m -> 0.01905 m.
2. SOR offset 0 => 100%; offset=c => 0%; offset=c/2 => 50%.
3. Rigid OD 0.2050 m in Dh=0.2159, Dc=0.1778 => 71.391076...% nominal geometric wall-contact SOR.
4. Dh<=Dc throws data error, does NOT return 0% standoff.
5. Rigid OD>Dh or below Dc is invalid, NOT silently clipped into apparent success.
6. Simply supported sag delta=5*q*L^4/(384*EI); q=100 N/m, L=10 m, EI=1e6 N*m2 => 0.0130208333 m. Double L => 16× deflection; q=0 => 0.
7. Midspan support ratio 100%, c=.02 m, delta=.01 m => screened midspan SOR 50%. Delta>.02 m => 0%, not negative.
8. For curve (0N,100%), (1000N,70%), (2000N,30%), interpolation 500N=>85%; 1500N=>50%; 3000N => UNKNOWN/no extrapolation.
9. One restoring-force test point only => no interpolated load curve/predicted bow SOR.
10. Survey straight vertical no dogleg => DLS 0; 0° to 90° over 300m => DLS 9°/30m. Handle azimuth 359° -> 1° wrap.
11. Unit conversions: 1 in = 0.0254 m, 1 ft=0.3048 m, 1 lbf=4.4482216152605 N; ~10ppg=1198.264273 kg/m3.
12. No NaN, Infinity or null-as-zero in displayed engineering results.

## Input and scenario tests
13. Reject survey duplicate/non-increasing MD, empty data, inclination 190°, unknown unit, missing columns.
14. Support a survey covering the entire analysis interval; if incomplete, flag no extrapolation.
15. Hole diameter section changes are applied at the correct depth boundary.
16. Rigid OD too large for narrow previous casing => incompatible.
17. Bow-spring free OD > restriction but compressed OD passes => review running/test conditions; do not automatically reject based on free OD alone.
18. Missing bow load curve => force-derived SOR hidden; show missing data and compatibility/BOM.
19. Every-2-joints pattern on an interval with 10 legal joints => deterministic exact joint indices and correct count; no index duplicates at boundaries.
20. 1, 2 and 3 joints patterns produce nonincreasing unit counts as k rises, within same interval/offset policy; results deterministic on repeat.
21. Stop collars per unit configurable; 0,1,2 plausible *catalog-approved* installation configurations; BOM uses specific per-SKU rule, not universal 2.
22. Editing one casing OD causes recalculation or invalidates stale results.
23. Save/load roundtrip (JSON), CSV export, browser PDF print preserved after reload.
24. Product with demo flag cannot be silently published as actual Sunshine SKU; prominent banner on PDF.
25. Reports display disclaimer, methodology, version/revision, input origin, catalog SKU, quantities, supporting test data references, missing-data notes and date.
26. Both metric and field UI yield numerically equivalent internal SI results.
27. Offline functionality: run build and app with network disabled; calculation still works.
28. Regression suite: all existing tests continue passing.

## Definition of done (R1)
A sales engineer can select actual approved SKU (if populated), enter client well geometry and optional survey, place centralizers on permitted joints, inspect constraints, compare 1/2/3-joint patterns, export installation plan/BOM and print a credible non-binding technical proposal. Unsupported physical predictions remain visibly unknown, not guessed.
