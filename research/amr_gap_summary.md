# India's Primary-Care AMR Surveillance Gap: One-Page Summary

## THE GAP NUMBER

# 80 percentage points
### (plausible range: 65–87.5 pp)

**~80% of India's antibiotic consumption happens in primary care/community settings** (Kotwani & Holloway,
BMC Infect Dis 2011, PMC3097160; corroborated in magnitude by the PharmaTrac retail-channel proxy, Koya et al.,
Lancet Reg Health SEA 2022, PMID 37383993), while **0% of specimens** feeding India's two flagship AMR
surveillance networks — ICMR AMRSN (21–29 sentinel hospitals, 2019–2023) and NCDC NARS-Net (13–54 sites,
2017–2024) — come from primary-care sites. Both networks are, by their own explicit statement, exclusively
tertiary-care/medical-college hospital networks in every year examined (`icmr_ncdc_india.json`).

The uncertainty range (65–87.5 pp) reflects the spread across four independent, non-equivalent consumption-side
proxies (direct community-use citation, retail-sales-channel share, single-facility outpatient share, private-vs-
public prescription share) — not a statistical confidence interval, since these are heterogeneous point estimates
rather than repeated samples of the same quantity. The surveillance-side term (0%) is an exact count, confirmed
across 12 site-years of primary-source ICMR/NCDC reports, with zero uncertainty.

---

## Chart 1: Where antibiotics are consumed vs. where surveillance happens

![Consumption vs surveillance split]({{artifact:dfa00f24-db89-471d-936a-3bcd8ee46f1e}})

## Chart 2: AMR sentinel networks have grown — but never toward primary care

![Sentinel site time series]({{artifact:6825dd32-92f9-42ee-8c05-7bccc9d40a08}})

## Chart 3: The geographic blind spot

![State-level blind spot scatter]({{artifact:82adf06f-f07e-423f-a9a2-3672080a3d8c}})

---

## Product positioning

Lipi's doctor-confirmed, longitudinal OPD prescribing and outcome data sits exactly where India's national AMR
surveillance infrastructure has zero visibility — at the point of care where roughly four in five Indian
antibiotic courses are actually prescribed. As decision support for doctors, not a replacement for microbiology,
a validated escalation-rate signal from Lipi's data could give prescribers and public-health partners an early,
low-cost read on local resistance pressure that today's hospital-only surveillance networks structurally cannot
provide until months later.

**Caveat:** this positioning is a hypothesis pending validation (`amr_study_protocol.md`) — Lipi's current data
streams are prescriptions, diagnoses, and follow-up outcomes, not microbiology culture results, so the signal
must be validated against real AMRSN/NARS-Net resistance data before being presented to doctors or partners as
established.

---
*Full analysis, source citations, and reproducible code: `amr_gap_analysis.ipynb`. Study design to validate this
positioning: `amr_study_protocol.md`.*
