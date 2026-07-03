# Study Protocol: Primary-Care Antibiotic Escalation as an Early-Warning Signal for Local AMR

**Prepared by:** Lipi Research
**Status:** Draft for internal review and institutional/ethics review board submission
**Related analysis:** `amr_gap_analysis.ipynb` (quantifies the surveillance gap this study addresses)

---

## 1. HYPOTHESIS

> **"Empirical antibiotic escalation in primary care (first-line → second-line for the same clinical syndrome,
> same patient, within 30 days) is a leading indicator of local antimicrobial resistance that precedes
> culture-based surveillance by N weeks."**

Where **N is a parameter to be estimated by this study**, not assumed. As a planning prior: India's flagship
hospital-based AMR surveillance networks (ICMR AMRSN, NCDC NARS-Net) publish **annual** aggregated reports
(see `amr_gap_analysis.ipynb`, Section 3) — meaning culture-based signals reach the public domain with a lag of
roughly 12 months from data collection to report publication. A prescribing-pattern signal computed from
near-real-time OPD data could plausibly lead this by weeks to low-single-digit months; **N is the primary
estimand of the Validation Approach (Section 3) below**, not a value we assert in advance.

**Rationale (from `amr_gap_analysis.ipynb`):** ~80% (range 65-87.5%) of India's antibiotic consumption occurs in
primary care/community settings (Kotwani & Holloway 2011, PMC3097160), while 0% of specimens feeding India's
two flagship AMR surveillance networks come from primary-care sites — both are exclusively tertiary-care/
medical-college hospital networks (ICMR AMRSN 2019-2023, NCDC NARS-Net 2017-2024). This creates a structural
blind spot: resistance trends may emerge in the community well before they are visible to hospital-based
surveillance, since hospital-referred cases are a late-stage, selected subset of community infections.

---

## 2. SIGNAL DEFINITION

**Escalation event:** A patient encounter in which a **second antibiotic course from a different (higher-line)
class** is prescribed for the **same clinical syndrome** in the **same patient**, within **30 days** of an initial
antibiotic prescription for that syndrome, where the second course is not explained by a documented adverse
drug reaction, allergy, or non-infectious diagnosis change.

**Syndrome definitions and line assignments** (source: [NCDC/ICMR National Treatment Guidelines for Antimicrobial
Use in Infectious Disease Syndromes](https://ncdc.mohfw.gov.in/wp-content/uploads/2025/12/National-Treatment-Guidelines-for-AMU-in-ID-syndromes-2025.pdf),
2016 original / 2025 revision — India's official standard-of-care reference, jointly published by NCDC and ICMR):

| Syndrome | First-line classes (India OPD) | Second-line / escalation classes | Notes |
|---|---|---|---|
| **URTI** (pharyngitis, acute bronchitis, non-severe sinusitis) | Amoxicillin, or no antibiotic (majority are viral) | Amoxicillin-clavulanate, macrolides (azithromycin), 2nd/3rd-gen cephalosporins | Per NCDC/ICMR guidelines, most URTIs do **not** warrant antibiotics; an escalation event requires an antibiotic was given both times |
| **UTI** (uncomplicated cystitis) | Nitrofurantoin, or fosfomycin (per NCDC/ICMR guidance) | Fluoroquinolones (ciprofloxacin/ofloxacin), 3rd-gen cephalosporins | Fluoroquinolone use as *initial* therapy is itself a stewardship flag, tracked separately from escalation |
| **Skin & soft tissue infection** (impetigo, cellulitis, abscess) | Amoxicillin-clavulanate, cephalexin/1st-gen cephalosporins | Clindamycin, fluoroquinolones, 3rd-gen cephalosporins | Per NCDC/ICMR SSTI chapter; treat for 5-7 days is the guideline default duration |
| **Enteric fever** (typhoid/paratyphoid, clinically diagnosed in OPD) | Cefixime (oral 3rd-gen cephalosporin), azithromycin | Fluoroquinolones (historically first-line, now escalation-flagged due to widespread resistance), carbapenems, ceftriaxone (IV, implies referral) | Enteric fever escalation to IV therapy or referral is itself a strong signal, tracked as a distinct sub-event |

**Operational rules for structured-data detection:**
1. **Same syndrome:** matched on Lipi's doctor-confirmed diagnosis code (ICD-10 or equivalent internal taxonomy),
   not free-text symptom matching, to avoid false-positive escalation from misclassified syndromes.
2. **Same patient:** matched on Lipi's patient identifier across visits at the same or different clinic within
   the network.
3. **Within 30 days:** the escalation window; chosen to capture a single "episode of illness" (initial Rx →
   follow-up due to non-response) while excluding unrelated re-infections. This window is a protocol parameter
   to be sensitivity-tested (7/14/30/60 days) once real data is available.
4. **Different (higher-line) class:** determined by the lookup table above, keyed to Lipi's structured medication
   field (drug name → ATC class mapping).
5. **Exclusion filter:** encounters where the follow-up record documents an explicit non-infectious reason for
   the second prescription (e.g., allergy, side effect, diagnosis correction) are excluded from the escalation
   numerator — this exclusion is itself a data field to be captured prospectively in Lipi's follow-up workflow.

**Escalation rate** for a district-quarter = (number of escalation events) / (number of initial antibiotic
courses for the 4 tracked syndromes in that district-quarter).

---

## 3. VALIDATION APPROACH

**Overlap identification:** Cross-reference Lipi's clinic locations (district/city level) against the 21 ICMR
AMRSN sentinel hospitals (2023) and 41 NCDC NARS-Net sentinel sites (2023) — see `icmr_ncdc_india.json`,
`state_level_site_distribution`, for the current published site list by state. Districts/cities where a Lipi
clinic operates within the same catchment area as an AMRSN/NARS-Net sentinel site are the study's **overlap
districts**.

**Correlation analysis:** For each overlap district, compute:
- **X = Lipi escalation rate** (Section 2), aggregated per district per reporting period (proposed: monthly,
  aggregated to quarterly for the primary analysis to match AMRSN/NARS-Net's typical reporting cadence).
- **Y = AMRSN/NARS-Net resistance rate** for the pathogen-antibiotic pair most relevant to each syndrome's
  escalation classes (e.g., E. coli fluoroquinolone resistance for UTI escalation; S. Typhi fluoroquinolone/
  cephalosporin resistance for enteric fever escalation), drawn from the corresponding sentinel hospital's
  published or requested antibiogram data for that district/region.

Compute the Pearson (or Spearman, if the resistance-rate distribution is non-normal) correlation between X and Y
across district-quarters, with a **pre-registered lag structure**: test correlation between X at time *t* and Y
at time *t+k* for k = 0, 4, 8, 12, ... weeks, to directly estimate the lead time.

**Lead-time estimation (operationalizing "N weeks"):** N is defined as the lag *k* (in weeks) at which the
cross-correlation between the escalation-rate signal and the AMRSN/NARS-Net resistance-rate signal is maximized
and statistically significant (p<0.05). This directly answers "how many weeks before AMRSN detects a spike does
our signal rise" as an empirical output of the study, not an input assumption.

**Pre-specified success criterion:** the hypothesis is considered supported if (a) the cross-correlation at the
optimal lag is statistically significant at the pre-registered alpha, (b) the optimal lag k > 0 (escalation leads
resistance detection, not the reverse), and (c) the effect replicates in a held-out set of overlap districts not
used for lag selection.

---

## 4. STATISTICAL POWER

**Sample size to detect a significant correlation** between district-level escalation rate and AMRSN/NARS-Net
resistance rate, computed via the Fisher z-transformation method (Cohen, 1988), two-tailed α=0.05, power=0.80:

$$n = \left(\frac{z_{1-\alpha/2} + z_{power}}{\text{atanh}(r)}\right)^2 + 3$$

| Correlation strength | r | Required district-quarter observation pairs (n) |
|---|---|---|
| Strong | 0.7 | **14** |
| Moderate | 0.5 | **30** |
| Weak | 0.3 | **85** |

*(Computed in `amr_gap_analysis.ipynb`-adjacent analysis using `scipy.stats.norm.ppf`; z_(1-α/2) = 1.9600, z_power = 0.8416.)*

**Patient-episodes needed per district-quarter:** the above n is the number of independent district-quarter
*pairs* needed for the correlation test itself — but each pair is an estimated escalation rate that must itself
be statistically stable. Assuming a baseline escalation rate of ~10% (a planning assumption to be replaced with
Lipi's own empirical rate once available) and requiring a 95% CI half-width ≤ 3 percentage points on that
estimate:

$$n_{episodes} = \frac{z_{1-\alpha/2}^2 \cdot p(1-p)}{\text{moe}^2} \approx \textbf{385} \text{ patient-episodes per district-quarter}$$

**Combined sample size requirement:**

| Scenario | District-quarter pairs | Episodes/district-quarter | Total patient-episodes |
|---|---|---|---|
| r=0.7 (strong) | 14 | 385 | **~5,390** |
| r=0.5 (moderate) | 30 | 385 | **~11,550** |
| r=0.3 (weak) | 85 | 385 | **~32,725** |

**Design implication:** if Lipi operates in ~5 districts that overlap with AMRSN/NARS-Net sentinel catchments,
a study spanning **3 quarters** yields 15 district-quarter pairs — sufficient to detect a strong correlation
(r=0.7, n=14 needed) but not a moderate one. Detecting r=0.5 requires either 6 quarters (18 months) at 5
districts, or recruiting more overlap districts in parallel. Detecting r=0.3 at 5 districts would require ~17
quarters (>4 years) — impractical; **the weak-correlation scenario should be treated as a "detect or rule out
a strong/moderate effect" design constraint, not a target for adequately-powered confirmation**, unless the
number of overlap districts can be substantially expanded (e.g., to ~28 districts over 3 quarters for r=0.3).

---

## 5. CONFOUNDERS TO CONTROL

1. **OTC antibiotic access before the visit.** A patient who self-medicated with an OTC antibiotic before
   presenting could show a "second-line" prescription that is not a true escalation-after-treatment-failure but
   a first clinician-guided choice reacting to prior unrecorded exposure. *Mitigation:* structured intake
   question on antibiotic use in the prior 14 days (already collectable at Lipi's point-of-care); flag and
   sensitivity-test with/without this subgroup.
2. **Seasonal infection surges (monsoon).** Enteric fever and UTI incidence rises during monsoon months in most
   Indian regions, which could independently drive both prescribing volume and (via more severe/complicated
   presentations) apparent escalation rates, confounding the resistance signal. *Mitigation:* include
   month-of-year as a covariate / use seasonally-adjusted escalation rates (e.g., deviation from each district's
   own 3-year seasonal baseline, once available).
3. **Drug stock-outs.** A prescriber may select a second-line drug simply because the first-line drug (e.g.
   nitrofurantoin, amoxicillin) is unavailable at the local pharmacy — a supply-side, not resistance-side,
   escalation driver. *Mitigation:* capture pharmacy-fulfilment/substitution notes where available; treat
   stock-out-flagged escalations as a distinct stratum, analyzed separately (see Negative Controls, Section 6).
4. **Individual prescriber idiosyncrasy.** Some clinicians may have a systematically higher baseline escalation
   tendency unrelated to local resistance (e.g., defensive prescribing, differing risk tolerance).
   *Mitigation:* include prescriber (or prescriber-clinic) as a random effect in a mixed-effects model, or
   analyze escalation rate at the clinic/district level (which averages out individual idiosyncrasy) rather than
   per-prescriber.
5. **Referral bias.** Sicker patients who are escalated may disproportionately be referred out of Lipi's network
   to hospitals — the same hospitals feeding AMRSN/NARS-Net — creating a mechanical (not epidemiological)
   correlation between "our escalation rate" and "their resistance rate" via shared patient flow, independent of
   true community resistance trends. *Mitigation:* track referral outcomes explicitly; run a sensitivity
   analysis excluding escalation events that culminate in referral, to confirm the correlation holds even in the
   non-referred (community-retained) subset.

---

## 6. NEGATIVE CONTROLS

**What would cause escalation WITHOUT true resistance, and how we distinguish it:**

| Negative-control driver | Expected signature if this (not resistance) is the cause | Distinguishing test |
|---|---|---|
| **Stock-outs** | Escalation rate spikes uniformly across *all* syndromes/antibiotic classes in a district simultaneously, tracks pharmacy supply-chain records, and reverts sharply once supply is restored (not gradually, as a true resistance trend would) | Cross-reference escalation spikes against Lipi's own pharmacy-availability/dispensing data (already part of the WhatsApp lab-dispatch integration context); a stock-out-driven spike should NOT correlate with AMRSN's resistance rate for the *specific* pathogen-drug pair |
| **Patient non-adherence** | Escalation is preceded by patient-reported early discontinuation or missed doses (captured via follow-up outcome data Lipi already collects), and is more common for longer-duration first-line regimens (e.g., 7-day skin infection courses) than short ones | Stratify escalation events by documented adherence status; a true resistance-driven signal should persist within the *adherent* subgroup |
| **Misdiagnosis** (e.g., viral URTI initially treated as bacterial, "escalated" when it doesn't improve, but was never a treatable bacterial infection) | Concentrated in syndromes where empiric treatment is inherently uncertain (URTI most of all, per NCDC/ICMR guidance that most URTIs are viral); should show no correlation with the specific bacterial-resistance metrics tracked by AMRSN (since there was no bacterial infection to resist) | Restrict the primary hypothesis test to syndromes with higher diagnostic certainty (UTI, enteric fever) as the primary analysis, with URTI reported as a secondary/exploratory analysis given its inherently noisier ground truth |
| **Seasonal/epidemic non-resistance-driven severity shifts** | Coincides with monsoon timing or a known local outbreak (e.g., a typhoid cluster from a contaminated water source) independent of any change in organism susceptibility | Covary for month and cross-check against public health department outbreak bulletins/IDSP alerts for the district; a true AMR-driven signal should not track outbreak-alert timing |

**Design principle:** none of these negative controls can be perfectly ruled out with prescription data alone —
this is an acknowledged limitation. The validation design's strength is in the **replication requirement**
(Section 3): a true resistance-driven escalation signal should (a) correlate with AMRSN/NARS-Net's independent,
microbiologically-confirmed resistance data, (b) persist across the confounder-adjusted sensitivity analyses in
Section 5, and (c) replicate out-of-sample. A negative-control-driven artifact would be expected to fail at
least one of these three tests.

---

## Appendix: Data sources cited in this protocol

- Surveillance network structure and site counts: `icmr_ncdc_india.json` (ICMR AMRSN annual reports, icmr.gov.in;
  NCDC NARS-Net annual reports, ncdc.mohfw.gov.in)
- Consumption-sector estimates: `consumption_india.json` (Kotwani & Holloway 2011, PMC3097160; Koya et al. 2022,
  PMID 37383993)
- Treatment-line definitions: [NCDC/ICMR National Treatment Guidelines for Antimicrobial Use in Infectious
  Disease Syndromes](https://ncdc.mohfw.gov.in/wp-content/uploads/2025/12/National-Treatment-Guidelines-for-AMU-in-ID-syndromes-2025.pdf)
  (2016 original, 2025 revision)
- Statistical power calculations: computed in this session via `scipy.stats`, method per Cohen (1988),
  *Statistical Power Analysis for the Behavioral Sciences*

**All numbers in Sections 1-4 above are either directly computed in this session or explicitly flagged as
planning assumptions to be replaced with empirical values once Lipi data collection begins.**
