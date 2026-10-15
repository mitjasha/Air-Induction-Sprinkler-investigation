# Publication-to-code evidence map

Reviewed 2026-10-15. Author identity was matched through the BSATU repository's full-name record, paper bylines and the user's supplied GitHub repository. The bibliography is a targeted selection, not a claim to cover every publication. Original-language titles, co-authors, source URLs and downloaded-file hashes are in [references.json](references.json); citations are also available as [BibTeX](references.bib).

## Eight relevant sources located

| Source | Evidence inspected and integration |
|---|---|
| Shakhrai & Basarevsky, 2017, [Анализ характеристик искусственного дождя при проектировании дождевальных машин](https://rep.bsatu.by/handle/doc/713), pp.384–387 | Quality-of-rain context; supports tracking intensity, coverage and drop characteristics separately. No coefficients imported. |
| Shakhrai, Basarevsky, Kravtsov & Popko, 2017, [Направления развития дождевальной техники](https://rep.bsatu.by/handle/doc/1791), pp.146–149 | Research context and adjustable-head direction; bibliography, not numerical validation. |
| Kravtsov, Basarevsky, Shakhrai & Popko, 2017, [Совершенствование насадок для широкозахватной дождевальной техники](https://rep.bsatu.by/handle/doc/1796), pp.149–152 | Related design paper; indexed and full text obtained. No distinct numerical calibration claimed. |
| Kravtsov, Shakhrai & Popko, 2017, [Дождевальная насадка с регулируемыми гидравлическими параметрами](https://rep.bsatu.by/handle/doc/2800), Agropanorama 5, pp.9–15 | Device, bench, volume-flow relations and trade-offs; measured curves retained as published qualitative evidence, not digitized raw data. |
| Kravtsov, Shakhrai, Basarevsky & Popko, 2018, [Исследование дождевальной насадки с регулируемыми гидравлическими параметрами](https://rgatu.ru/archive/sborniki_konf/25_04/sbor_2.pdf), printed pp.175–179 | Related bench study; confirms observables and design objectives. These related reports must not be counted as independent datasets without run provenance. |
| Shakhrai, Kravtsov & Basarevsky, 2018, [Анализ факторов, влияющих на размер капель искусственного дождя, образованного дефлекторными насадками](https://rep.bsatu.by/handle/doc/5684), pp.382–386 | Similarity approach and film-to-drop research context. Eq.1 explicitly includes C, supporting investigation of a missing prefactor without confirming its value. |
| Basarevsky, Kravtsov & Shakhrai, 2019, [Критериальное уравнение подобия для определения диаметра капель искусственного дождя](https://doi.org/10.29235/1817-7204-2019-57-2-230-237), Proceedings of the National Academy of Sciences of Belarus, Agrarian Series 57(2), pp.230–237 | Original Eqs.18–20, eight-row source transcription and separately labeled C=0.001 hypothesis; no confirmed correction claimed. |
| Kravtsov & Shakhrai, 2021, [Совершенствование дождевальных машин применением дождеобразующих устройств с регулируемыми гидравлическими характеристиками](https://rep.bsatu.by/handle/doc/12545), Agropanorama 1, pp.14–18 | Eqs.1–6 implemented as a flow contract; water/air valve and sensor architecture informs the automation roadmap. |

## Executable 2019 audit

Run from the repository root:

    python examples/literature_audit.py --output artifacts/literature

The script produces comparison.csv, audit.json, [comparison.md](literature/comparison.md), comparison.png and comparison.svg. Both variants use the exact printed signs in Eqs.18–20, d0 in metres (the definition on p.232), L=d0, alpha=1 and the rounded Oh/Fr entries of Table 1. Here Fr=v²/(gL), rather than the alternative square-root convention. The exponent slopes are dimensional inverse-metre constants.

The literal result remains approximately 980–1023 times the tabulated calculation. A second API, criterion_2019_c001_hypothesis, multiplies that unchanged SI result by a fixed dimensionless C=0.001. This is an explicit correction hypothesis requested by the author, not an established erratum. It is isolated from the forward and inverse models. Per-row implied C values are diagnostics and never used to tune a prediction.

This source-specific C is separate from the demonstration breakup coefficient fitted by the calibrate command.

## Unit check and C=0.001 hypothesis

Printed Eq.18 is dk = L*(alpha*Fr/2)^x1*(1/Oh²)^x5. All factors except L are dimensionless, so dk and L have the same length unit. A consistent unit conversion cannot change dk/L. The proposed variant is dk_hyp = C*L*(alpha*Fr/2)^x1*(1/Oh²)^x5, with dimensionless C=0.001.

For the first row, d0=L=0.00298 m, Fr=4178, Oh=0.0022 and alpha=1 give x1=0.206523424, x5=0.301599098. The two factors are 4.848920392 and 40.090903584. Their product is 194.397599935. Thus the printed result is 0.579304848 m = 579.304848 mm; the hypothesis gives 0.000579305 m = 0.579305 mm, compared with the paper's calculated 0.58 mm. The reported experimental value for that row is 0.70 mm.

When using nozzle numbers in mm, the exponent slopes must also change: x1=-0.0088512*d0_mm+0.2329 and x5=-0.0009399*d0_mm+0.3044. Substituting 2.98 into the original SI slopes is inconsistent. The near-1000 mismatch could reflect a missing prefactor or a numeric metre result labeled as millimetres; the original calculation sheet is needed to distinguish these explanations. The 2018 expression includes C but does not establish C=0.001 for the 2019 fit.

| Reference column, all eight rows | Hypothesis MAPE | Hypothesis MAE | Maximum absolute relative error |
|---|---:|---:|---:|
| Published calculation | 1.1109% | 0.012718 mm | 2.3361% |
| Reported experiment | 15.6113% | 0.168994 mm | 23.0788% |

The full [eight-row table](literature/comparison.md) preserves the literal result and both reference columns. The figures show the original scale, the hypothesized scale, and signed errors against each distinct reference. These metrics describe source reproduction and descriptive agreement with reused literature data; they are not predictive holdout accuracy.

All eight hypothesis intervals overlap the published calculation intervals if displayed values were rounded to nearest: Oh ±0.00005, Fr ±0.5 and the published calculation ±0.005 mm. Only Oh and Fr are varied in the hypothesis bounds; nozzle/exponent precision is held fixed. This establishes compatibility with those explicit rounding assumptions, not the actual rounding method or measurement uncertainty. The original approximately 1000x discrepancy cannot be explained by rounding alone.

Python APIs (both return metres):

    from sprinkler1d.literature import criterion_2019, criterion_2019_c001_hypothesis
    args = (0.00298, 4178, 0.0022, 0.206523424, 0.301599098)
    print(criterion_2019(*args))                  # 0.579304847807418
    print(criterion_2019_c001_hypothesis(*args))  # 0.000579304847807418

The paper attributes the experimental column to Kincaid, Solomon & Oliphant (1996), *Drop size distributions for irrigation sprinklers*, Transactions of the ASAE 39(3), 839–845, DOI 10.13031/2013.27568. That original dataset has not been recovered here. The paper also derives its exponent fits from experimental values, so its own table cannot be treated as an independent holdout. The generic paper diameter dk is not silently converted into this solver's d32. Published table conditions (nozzles 2.98–9.15 mm, pressures 69 and 206 kPa) describe the source comparison, not a validated design envelope.

## Source-backed hydraulic and automation contract

The 2021 relations calculate k=Qa/Qw, Vw=Qw/A, Vmix=(Qw+Qa)/A and n-head flow totals. These are accounting identities for a common local gas-volume reference and homogeneous-flow interpretation. They do not determine suction pressure, required pump energy, branch-flow maldistribution, actuator response or achievable entrainment. The example's 12 heads and flow values are invented demonstration inputs and explicitly labeled as such.

The 2017 bench compared a Nelson Rotator 3030 with and without the ejector. It reports different favourable nozzle diameters for head loss (8.6 mm) and entrainment/electrical pump power (7.9 mm), with observed k at most 0.5 in that series. Those findings motivate a future multi-objective calibration; they do not establish the optimum for the present demonstration geometry. Pump electrical power must be measured separately from hydraulic power pQ.

## Physical regime and unresolved evidence

The 2021 text describes direct breakup after the deflector in aerated operation without a free sheet. The current attached radial-film block and empirical breakup closure therefore require regime-specific observation; they are not a verified transcription of that mechanism. The 2019 expression has no explicit air-entrainment input and cannot establish an air-induced size reduction by itself.

The 2021 bibliography mentions BY 22927 and BY 22747. Their primary patent texts and current status have not been checked and no patent-claim or freedom-to-operate conclusion is made. MIT covers this new software, not third-party article content or hardware patent rights.

Next evidence needed: original 2019 calculation workbook; precise drop-size statistic; run-level pressure, water/air flow and pump-power records with gas reference conditions; dimensioned CAD and valve settings; film/breakup video; independently held-out droplet and catch-can measurements. Dissertation and author abstract remain pending upload.
