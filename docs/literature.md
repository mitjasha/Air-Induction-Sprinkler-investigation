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
| Shakhrai, Kravtsov & Basarevsky, 2018, [Анализ факторов, влияющих на размер капель искусственного дождя, образованного дефлекторными насадками](https://rep.bsatu.by/handle/doc/5684), pp.382–386 | Similarity approach and film-to-drop research context. Its Eq.1 includes a prefactor C; this is not silently inserted into the later 2019 expression. |
| Basarevsky, Kravtsov & Shakhrai, 2019, [Критериальное уравнение подобия для определения диаметра капель искусственного дождя](https://doi.org/10.29235/1817-7204-2019-57-2-230-237), Proceedings of the National Academy of Sciences of Belarus, Agrarian Series 57(2), pp.230–237 | Printed Eqs.18–20 implemented in literature.py; Table 1 transcribed; explicit reproduction discrepancy. |
| Kravtsov & Shakhrai, 2021, [Совершенствование дождевальных машин применением дождеобразующих устройств с регулируемыми гидравлическими характеристиками](https://rep.bsatu.by/handle/doc/12545), Agropanorama 1, pp.14–18 | Eqs.1–6 implemented as a flow contract; water/air valve and sensor architecture informs the automation roadmap. |

## Executable 2019 audit

Run from the repository root:

    python examples/literature_audit.py --output artifacts/literature

The script produces comparison.csv, audit.json and comparison.png. It uses the exact printed signs in Eqs.18–20, d0 in metres (the definition on p.232), L=d0, alpha=1 and the rounded Oh/Fr entries of Table 1. Here Fr=v²/(gL), rather than the alternative square-root convention. The exponent slopes are dimensional inverse-metre constants.

The literal result is approximately 980–1023 times the tabulated calculation. This near-1000 factor suggests a unit-scale or prefactor issue worth checking, but its cause is not established. The automated test records this unresolved reproducibility problem; passing the test does **not** mean the article's correlation was validated. Rounding alone cannot account for that scale of mismatch. No corrected formula is proposed without the author's calculation sheets or an erratum. The 2018 prefactor is a possible item to investigate, not an established correction.

The paper attributes the experimental column to Kincaid, Solomon & Oliphant (1996), *Drop size distributions for irrigation sprinklers*, Transactions of the ASAE 39(3), 839–845, DOI 10.13031/2013.27568. That original dataset has not been recovered here. The paper also derives its exponent fits from experimental values, so its own table cannot be treated as an independent holdout. The generic paper diameter dk is not silently converted into this solver's d32. Published table conditions (nozzles 2.98–9.15 mm, pressures 69 and 206 kPa) describe the source comparison, not a validated design envelope.

## Source-backed hydraulic and automation contract

The 2021 relations calculate k=Qa/Qw, Vw=Qw/A, Vmix=(Qw+Qa)/A and n-head flow totals. These are accounting identities for a common local gas-volume reference and homogeneous-flow interpretation. They do not determine suction pressure, required pump energy, branch-flow maldistribution, actuator response or achievable entrainment. The example's 12 heads and flow values are invented demonstration inputs and explicitly labeled as such.

The 2017 bench compared a Nelson Rotator 3030 with and without the ejector. It reports different favourable nozzle diameters for head loss (8.6 mm) and entrainment/electrical pump power (7.9 mm), with observed k at most 0.5 in that series. Those findings motivate a future multi-objective calibration; they do not establish the optimum for the present demonstration geometry. Pump electrical power must be measured separately from hydraulic power pQ.

## Physical regime and unresolved evidence

The 2021 text describes direct breakup after the deflector in aerated operation without a free sheet. The current attached radial-film block and empirical breakup closure therefore require regime-specific observation; they are not a verified transcription of that mechanism. The 2019 expression has no explicit air-entrainment input and cannot establish an air-induced size reduction by itself.

The 2021 bibliography mentions BY 22927 and BY 22747. Their primary patent texts and current status have not been checked and no patent-claim or freedom-to-operate conclusion is made. MIT covers this new software, not third-party article content or hardware patent rights.

Next evidence needed: original 2019 calculation workbook; precise drop-size statistic; run-level pressure, water/air flow and pump-power records with gas reference conditions; dimensioned CAD and valve settings; film/breakup video; independently held-out droplet and catch-can measurements. Dissertation and author abstract remain pending upload.
