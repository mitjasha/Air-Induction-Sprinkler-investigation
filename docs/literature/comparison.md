# Eight-row comparison: unconfirmed C=0.001 hypothesis

Original equation retained. All diameters below are in mm. Errors are signed.

| Row | Nozzle | p [kPa] | Reported experiment | Published calculation | Literal C=1 | Hypothesis C=0.001 | Error vs calculation [%] | Error vs experiment [%] |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 2.98 | 69 | 0.70 | 0.58 | 579.305 | 0.579305 | -0.120 | -17.242 |
| 2 | 4.57 | 69 | 0.94 | 0.82 | 813.824 | 0.813824 | -0.753 | -13.423 |
| 3 | 6.12 | 69 | 1.08 | 1.02 | 1025.558 | 1.025558 | +0.545 | -5.041 |
| 4 | 9.06 | 69 | 1.63 | 1.28 | 1253.815 | 1.253815 | -2.046 | -23.079 |
| 5 | 3.07 | 206 | 0.68 | 0.75 | 737.568 | 0.737568 | -1.658 | +8.466 |
| 6 | 4.61 | 206 | 0.86 | 1.02 | 1008.094 | 1.008094 | -1.167 | +17.220 |
| 7 | 6.22 | 206 | 1.03 | 1.25 | 1253.282 | 1.253282 | +0.263 | +21.678 |
| 8 | 9.15 | 206 | 1.31 | 1.52 | 1555.509 | 1.555509 | +2.336 | +18.741 |

Comparison with published calculation: MAPE=1.1109%; MAE=0.012718 mm; RMSE=0.017041 mm; maximum absolute relative error=2.3361%.

Comparison with reported experiment: MAPE=15.6113%; MAE=0.168994 mm; RMSE=0.196959 mm; maximum absolute relative error=23.0788%.

All eight published calculation intervals overlap the hypothesis intervals under the explicitly assumed display-rounding bounds in audit.json. This is a precision compatibility check, not a measurement uncertainty assessment.

C=0.001 is fixed for this hypothesis. Per-row implied C values in comparison.csv are diagnostics only. The original workbook or a confirmed erratum is still needed.

Source: [2019 paper, Table 1 and Eqs.18–20](https://doi.org/10.29235/1817-7204-2019-57-2-230-237).
