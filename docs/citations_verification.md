# Citations for Verification

Papers to verify before adding to thesis bibliography. Check DOI resolves and authorship is correct.

---

## Existing thesis citations (confirmed previously)

| Key | Authors | Title | DOI |
|-----|---------|-------|-----|
| lasek2016 | Lasek et al. | Restaurant sales forecasting | 10.1007/978-3-319-33681-7_40 |
| wu2024 | Wu et al. | Restaurant demand prediction | 10.1016/j.ijhm.2024.103750 |
| lee2018 | Lee et al. | Tourism demand forecasting | 10.1016/j.tourman.2017.11.004 |
| sun2019 | Sun et al. | Tourism demand ML | 10.1016/j.tourman.2018.07.010 |
| liu2025 | Liu et al. | Hotel demand forecasting | 10.1108/JHTT-01-2024-0028 |
| choi2009 | Choi, Hwang & Park | Scheduling restaurant workers | 10.1177/1938965509333557 |
| bergmeir2012 | Bergmeir & Benítez | Neural networks for time series | 10.1016/j.ins.2011.12.028 |
| kimes1989 | Kimes | Revenue management | 10.1016/0272-6963(89)90035-1 |
| strobl2007 | Strobl et al. | Bias in random forest variable importance | 10.1186/1471-2105-8-25 |
| breiman2001 | Breiman | Random forests | Machine Learning 45(1):5–32 |
| ernst2004 | Ernst et al. | Staff scheduling and rostering | 10.1016/S0377-2217(03)00095-X |
| bergh2013 | Van den Bergh et al. | Personnel scheduling: a literature review | 10.1016/j.ejor.2012.11.029 |
| thompson2004 | Thompson | Restaurant scheduling | Cornell Hospitality Report 4(6):7–55 |
| thompson2008 | Thompson | Restaurant scheduling tools | Cornell Hospitality Report 8(16):4–11 |
| rossi2006 | Rossi et al. | Handbook of Constraint Programming | Elsevier |
| wtd2003 | EU | Working Time Directive 2003/88/EC | — |
| hungarian2012 | Hungarian Parliament | Labour Code Act I of 2012 | — |
| ortools2024 | Google | OR-Tools | https://developers.google.com/optimization |
| bensaid2024 | Bensaid et al. | — | arXiv:2409.07547 |
| lu2023 | Lu et al. | — | arXiv:2302.04062 |
| heliyon2023 | — | — | 10.1016/j.heliyon.2023.e18385 |
| pmc2025 | — | — | 10.1007/s10068-025-01956-2 |

---

## New papers — adoption gap claim

Supporting: *"The methods required for demand-responsive scheduling have been available for over a decade yet adoption remains limited; the gap is organisational/financial, not technological."*

---

### thompson2003
**Thompson, Gary M. (2003)**
"Labor Scheduling: A Commentary"
*Cornell Hotel and Restaurant Administration Quarterly*, Vol. 44, Nos. 5–6, pp. 149–155
DOI: `10.1177/001088040304400520`
**Supports:** Establishes that quantitative demand-driven labor scheduling methods were fully developed and documented by 2003 — over a decade before current practice — forming the "available for over a decade" baseline.
**Confidence:** High

---

### rocha2012
**Rocha, Marta; Oliveira, José Fernando; Carravilla, Maria Antónia (2012)**
"Quantitative Approaches on Staff Scheduling and Rostering in Hospitality Management: An Overview"
*American Journal of Operations Research*, Vol. 2, No. 1, pp. 137–145
DOI: `10.4236/ajor.2012.21016`
**Supports:** Catalogues over a decade of validated quantitative scheduling methods for hospitality; the fact that an overview paper was needed implies the methods existed but had not been consolidated into practice.
**Confidence:** High

---

### ivanov2021
**Ivanov, Stanislav; Del Chiappa, Giacomo; Heyes, Andy (2021)**
"The Research-Practice Gap in Hotel Revenue Management: Insights from Italy"
*International Journal of Hospitality Management*, Vol. 95, Article 102924
DOI: `10.1016/j.ijhm.2021.102924`
**Supports:** Documents that even revenue management — the sophisticated side of the contrast — shows a research-practice gap driven by organisational characteristics (size, chain affiliation), not technology. Strengthens the "organisational, not technological" framing.
**Confidence:** High

---

### okumus2017
**Okumus, Fevzi; Bilgihan, Anil; Ozturk, Ahmet Bulent; Zhao, Xinyuan (2017)**
"Identifying and Overcoming Barriers to Deployment of Information Technology Projects in Hotels"
*Journal of Organizational Change Management*, Vol. 30, No. 5, pp. 744–766
DOI: `10.1108/JOCM-12-2015-0239`
**Supports:** Directly documents that the primary barriers to hotel IT adoption are organisational and financial (cost/ROI concerns, executive resistance, training gaps) — not technological capability. Most direct support for the "not primarily technological" framing.
**Confidence:** High

---

### thompson1998
**Thompson, Gary M. (1998)**
"Labor Scheduling, Part 1: Forecasting Demand"
*Cornell Hotel and Restaurant Administration Quarterly*, Vol. 39, No. 5, pp. 22–31
DOI: `10.1177/001088049803900507`
**Supports:** The 1998 anchor for "available for over a decade" — a four-part peer-reviewed series in Cornell HRAQ that formalised an eight-step demand-forecasting framework explicitly for hospitality labor scheduling. Methods were already mature enough for multi-installment academic treatment by 1998.
**Confidence:** High

---

### schmidt2022
**Schmidt, Alexander; Kabir, M. W. Ullah; Hoque, Mohammad Enamul (2022)**
"Machine Learning Based Restaurant Sales Forecasting"
*Machine Learning and Knowledge Extraction*, Vol. 4, No. 1, pp. 105–130
DOI: `10.3390/make4010006`
**Supports:** Validates LSTM, Temporal Fusion Transformer, and ensemble ML models on three years of real single-restaurant sales data (sMAPE as low as 19.6%), confirming that ML-based demand-responsive scheduling methods are empirically validated in restaurant settings.
**Confidence:** High

---

### gans2015
**Gans, Noah; Shen, Haipeng; Zhou, Yong-Pin; Korolev, Nikolay; McCord, Alan; Ristock, Herbert (2015)**
"Parametric Forecasting and Stochastic Programming Models for Call-Center Workforce Scheduling"
*Manufacturing & Service Operations Management*, Vol. 17, No. 4, pp. 571–588
DOI: `10.1287/msom.2015.0546`
**Supports:** Validates stochastic optimisation-based workforce scheduling on two large real service-operation datasets, with stable cost-reducing solutions — operationally analogous to hospitality given shared demand-uncertainty and service-level structure. Establishes method maturity by 2015.
**Confidence:** High

---

## Adversarial research note

The deep research agent ran 3-judge adversarial verification on all papers above. Key finding:

**Strong support:** "Methods have been available for over a decade" (thompson1998, gans2015, schmidt2022, choi2009 already in bibliography).

**Weak/indirect support:** "Adoption remains limited; gap is organisational/financial not technological." No paper was found that *directly measures* adoption rates of demand-responsive scheduling or *names* organisational barriers as primary over technological ones specifically for workforce scheduling. The organisational-barriers evidence (okumus2017, ivanov2021) is from IT adoption and revenue management respectively — not workforce scheduling specifically.

**Implication for thesis:** The claim as written is partially overclaimed. Consider softening to: "…yet their uptake in workforce planning has lagged behind revenue management, a pattern consistent with the organisational and financial barriers documented more broadly in hospitality technology adoption \citep{okumus2017, ivanov2021}."
