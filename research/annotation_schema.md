## Literature Synthesis (What Transfers, What Breaks, What Is New)

**NegEx (Chapman et al. 2001, *J Biomed Inform* 34(5):301-310).** NegEx implements a small set of
regular-expression negation phrases split into pre-condition triggers ("no", "denies", "ruled out"),
post-condition triggers ("was ruled out", "negative for"), and pseudo-negation phrases that look like
negation but aren't ("not only", "no increase"). Scope is a fixed six-token window around the trigger.
On 1,235 discharge-summary findings it reached 84.5% PPV and 77.8% sensitivity against a physician
gold standard. **What transfers to Hinglish:** the core idea — negation is a departure from a default
affirmed state, triggered by a short closed list of words — is language-agnostic and maps cleanly onto
"nahi/nahin" as the Hindi analogue of "no/not". **What breaks:** the six-token window assumes
head-initial English word order; Hindi is SOV, so "nahi" characteristically sits *after* the object and
*before* the verb ("dard nahi hai" = pain not is), and code-switched clauses freely interleave both
orders within one sentence — a fixed window calibrated on English syntax will clip or overshoot scope.

**ConText (Harkema et al. 2009, *J Biomed Inform* 42(5):839-851).** ConText extends NegEx with
Temporality (historical/hypothetical, default recent) and Experiencer, replacing the six-token window
with scope-to-termination-term-or-sentence-end. Averaged across six report types it reached
0.93 F1 for Negation but only 0.76 F1 for Historical and 0.86 for Hypothetical; inter-annotator kappa
for Historical was just 0.35 versus 0.74 for Negation, because the dominant trigger "history" is
lexically ambiguous (a section header vs. an actual temporal marker) and its correct scope often spans
a whole discourse segment rather than a phrase. **What transfers:** the finding that trigger-word
approaches degrade sharply once scope stops being local — the same failure mode is expected for
Hinglish "pehle" (before), which is similarly overloaded ("pehle se" as intensifier vs. genuine
temporal marker). **What's genuinely new:** ConText's termination-term apparatus was built for
paragraph-structured written notes with section headers; OPD transcripts are turn-based dialogue with
no such structure, so termination cues must instead come from turn boundaries and conjunctions
("lekin", "phir").

**i2b2 2010 Assertion Challenge (Uzuner et al. 2011, *JAMIA* 18(5):552-556).** Six categories —
present, absent, possible, conditional, hypothetical, associated-with-someone-else — over 18,550
assertions (13,025 present, 3,609 absent, 883 possible, 717 hypothetical, 171 conditional, 145
associated-with-someone-else). The best system scored 0.931 F1, but *conditional* was the hardest
category by a wide margin: rule-based systems frequently mis-tagged *present* as *conditional*, and
the two top systems shared only 31 overlapping conditional annotations. **What transfers:** rare,
low-support categories are where rule-based and ML systems diverge most — the direct analogue for us
is "queried" and "planned", the least frequent states in real OPD speech. **What's new for Hinglish:**
i2b2's categories collapse epistemic and temporal status into one axis; OPD consultation demands both
independently (a fact can be uncertain *and* historical at once), which the i2b2 schema cannot express.

**THYME (Styler et al. 2014, *TACL* 2:143-154).** Extends ISO-TimeML for clinical narratives with
EVENT/TIMEX3/DOCTIME spans linked by TLINKs (temporal order) and ALINKs (aspect), distinguishing
linguistically-derived from inferentially-derived orderings. **What transfers:** anchoring every fact
to document/consultation creation time (DOCTIME) is exactly the right primitive for OPD dialogue —
"abhi" and "ab" are BEFORE/OVERLAP relations to the moment of speech. **What breaks:** THYME's
full TLINK graph is annotated on written oncology notes with paragraph-level context; a real-time OPD
turn has no equivalent discourse scaffold, so only a coarse 3-way historical/current/planned
simplification is tractable at the point of extraction.

**Code-switching NLP (Bali et al. 2014; Srivastava & Singh 2021; Khanuja et al. 2020, GLUECoS).**
Hindi and English are syntactically divergent (SOV vs. SVO), unlike Spanglish, which shares SVO order —
Hinglish code-mixing is therefore structurally harder to parse than most other code-switched pairs.
Token-level language identification remains unreliable and complexity metrics like CMI are unstable
under simple word reordering, meaning any pipeline stage that assumes consistent script or word order
per clause is fragile. **Genuinely new problem:** no published corpus annotates negation, epistemic
modality, or temporality specifically for Hindi-English code-switched *clinical* speech — this is an
open gap our synthetic set and rule-based baseline are designed to probe, not a validated benchmark.


## Annotation Schema

# Hinglish Clinical Epistemic × Temporal Annotation Schema

**Project:** Lipi deterministic clinical extractor — Hinglish upgrade
**Scope:** Classifying the epistemic and temporal state of a clinical fact (symptom, diagnosis, vital,
medication, test) as spoken in Hindi-English code-switched Indian OPD consultations.
**Status:** Draft v1, synthetic-data validated only. No real transcript data used — see gap flags below.

---

## 1. Why two axes

Our current pipeline has a single epistemic axis (affirmed/negated/uncertain/queried) and no temporal
axis. Both i2b2 2010's `assertion` categories and ConText's `Negation`/`Temporality` properties conflate
epistemic status and time-reference into overlapping single-axis category systems (e.g., i2b2's
`hypothetical` mixes "not yet true" with "will happen in future"). OPD consultations need the two axes
kept independent because either can vary while the other stays fixed — "Pehle sugar high tha" (historical,
affirmed) and "Shayad sugar thoda high hai" (current, uncertain) are different failures of our current
single-axis pipeline, and neither is expressible as one flag.

- **Epistemic axis** — how committed is the speaker to the fact being true:
  - `affirmed` — stated as true, no hedge, no negation, not posed as a question.
  - `negated` — explicitly stated as false/absent.
  - `uncertain` — hedged: speaker believes it may be true but does not commit ("shayad", "lagta hai").
  - `queried` — posed as a question; status is unresolved pending an answer (by doctor to patient or
    vice versa), distinct from `uncertain` because the speaker is not asserting a belief at all.
- **Temporal axis** — when does/did the fact hold, relative to the moment of speech (≈ DOCTIME in
  THYME's terms):
  - `historical` — held before the current visit/consultation; not asserted to still hold now.
  - `current` — holds at the time of speech / during the present visit.
  - `planned` — to occur or be checked/started at a future point (next visit, after a test, once a
    medicine course finishes).

4 epistemic × 3 temporal = **12 combinations**, all of which are logically constructible and are used in
the synthetic test set. Two combinations are rare/degenerate in real OPD speech and need special
annotation care (documented in §3); none are excluded from the tag set.

---

## 2. The 12 tags

### 1. `affirmed_historical`

**Definition:** Fact is asserted as true and is explicitly placed before the current visit; not claimed to still hold now.

**Examples:**
- Pehle **sugar** high tha, ab control mein hai.  _(entity: sugar/diabetes)_
- Do saal pehle mujhe **TB** hua tha.  _(entity: tuberculosis)_
- Last month **bukhar** aaya tha, teen din raha.  _(entity: fever)_

**Decision rule:** Affirmative verb/clause with a historical-signal word ('pehle', 'tha', 'hua tha', 'purana') AND no negation or hedge word in scope. If a later clause in the same sentence gives a current update, split into two facts (see Hard Cases §5, multi-clause rule).

### 2. `affirmed_current`

**Definition:** Fact is asserted as true and holds now / during the present visit. This is the default, most frequent OPD state.

**Examples:**
- Abhi **BP** 150/90 chal raha hai.  _(entity: BP)_
- Aaj kal **khansi** bahut zyada hai.  _(entity: cough)_
- Filhaal **weight** 68 kilo hai.  _(entity: weight)_

**Decision rule:** Affirmative clause with present-tense copula ('hai', 'chal raha hai') and/or current-signal word ('abhi', 'aaj kal', 'filhaal'), with no historical or planned marker and no negation/hedge.

### 3. `affirmed_planned`

**Definition:** Fact/action is asserted as something that will happen or be done in the future — a prescribed plan, not yet executed.

**Examples:**
- Agle hafte **sugar test** karwa lo.  _(entity: test result)_
- Kal se yeh **medicine** shuru karna hai.  _(entity: medication)_
- Next week **follow-up** ke liye aana hai.  _(entity: follow-up)_

**Decision rule:** Affirmative clause with future/imperative-plan marker ('karwa lo', 'karna hai', 'agle hafte', 'next time', 'will'), referring to an action not yet done.

### 4. `negated_historical`

**Definition:** Fact is explicitly denied as having held in the past — the patient did NOT have/experience it before.

**Examples:**
- Pehle kabhi **allergy** nahi thi.  _(entity: allergy)_
- Purana koi **BP** ki problem nahi thi.  _(entity: BP)_
- Pehle **surgery** nahi hui thi.  _(entity: surgery/procedure)_

**Decision rule:** Negation-signal word ('nahi', 'nahi thi/tha') co-occurring with a historical-signal word ('pehle', 'purana', 'kabhi'), scoped over the same clause.

### 5. `negated_current`

**Definition:** Fact is explicitly denied as holding right now.

**Examples:**
- Dard nahi hai ab.  _(entity: pain)_
- Abhi **bukhar** bilkul nahi hai.  _(entity: fever)_
- Sugar ab high nahi hai, normal hai.  _(entity: sugar/diabetes)_

**Decision rule:** Negation-signal word in the same clause as a current-signal word or bare present-tense copula, no historical/planned marker. This is the single highest-risk pattern for our pipeline: negation placed AFTER the entity and BEFORE the current marker ('dard nahi hai ab') is where scope currently gets lost.

### 6. `negated_planned`

**Definition:** A planned action or expected future fact is explicitly declined/ruled out. Rare in OPD speech but occurs when a doctor rules out a future test/treatment or a patient declines a plan.

**Examples:**
- Abhi **operation** ki zaroorat nahi hai, next visit dekhenge.  _(entity: diagnosis/procedure)_
- Agle hafte **test** repeat nahi karna, filhaal theek hai.  _(entity: test result)_
- Yeh **medicine** aage nahi denge.  _(entity: medication)_

**Decision rule:** Negation word scoped over a planned/future-signal clause. RARE — see §3 rationale. Do not confuse with negated_current answered about a plan already dismissed as unnecessary (which is negated_planned) vs. a plan being stopped as of now (negated_current, e.g. 'ab yeh dawai nahi de rahe' = stopping now).

### 7. `uncertain_historical`

**Definition:** Speaker hedges about whether something happened in the past; not fully committed, but also not denying it.

**Examples:**
- Shayad pehle bhi **BP** thoda high tha.  _(entity: BP)_
- Lagta hai purane time mein **sugar** ki problem thi.  _(entity: sugar/diabetes)_
- Maybe pehle kabhi **chest pain** hua tha, yaad nahi.  _(entity: chest pain)_

**Decision rule:** Uncertainty-signal word ('shayad', 'lagta hai', 'maybe', 'yaad nahi') co-occurring with a historical-signal word, no explicit negation.

### 8. `uncertain_current`

**Definition:** Speaker hedges about whether something holds right now — the most common uncertain state, e.g., a patient's vague self-report.

**Examples:**
- Shayad BP thoda high hai.  _(entity: BP)_
- Lagta hai thoda **fever** hai abhi.  _(entity: fever)_
- Weight thoda badha hua sa laga is hafte.  _(entity: weight)_

**Decision rule:** Uncertainty-signal word ('shayad', 'thoda', 'lagta hai', 'laga', 'feel ho raha hai') in the same clause as a current/default-tense marker, no negation and no explicit question form.

### 9. `uncertain_planned`

**Definition:** Speaker hedges about whether a future action/plan will happen — tentative plans, not yet firmly committed.

**Examples:**
- Shayad agle hafte **test** karwana padega.  _(entity: test result)_
- Ho sakta hai **dawai** badalni pade next time.  _(entity: medication)_
- Lagta hai **follow-up** thodi der mein karna pad sakta hai.  _(entity: follow-up)_

**Decision rule:** Uncertainty-signal word combined with a future/plan marker ('agle hafte', 'next time', 'padega', 'pad sakta hai'); modal 'padega/pad sakta hai' (may need to) is a strong planned+uncertain combination cue.

### 10. `queried_historical`

**Definition:** A question is posed about whether something held in the past — status unresolved, distinct from uncertain (no belief is asserted, only a question).

**Examples:**
- Pehle kabhi **sugar** ki problem thi kya?  _(entity: sugar/diabetes)_
- Kya aapko purana **allergy** tha?  _(entity: allergy)_
- Pehle **operation** hua tha kya aapka?  _(entity: surgery/procedure)_

**Decision rule:** Question marker ('kya', 'kya...?', rising-intonation transcription cue, or explicit '?') co-occurring with a historical-signal word. RARE — see §3 rationale; mostly doctor-initiated history-taking questions.

### 11. `queried_current`

**Definition:** A question is posed about whether something holds right now.

**Examples:**
- Abhi **dard** hai kya?  _(entity: pain)_
- BP aaj check kiya kya, kitna hai?  _(entity: BP)_
- Kya abhi bhi **khansi** hai?  _(entity: cough)_

**Decision rule:** Question marker in the same clause as a current-signal word or bare present tense; this is the most frequent queried state (doctor asking about present symptoms).

### 12. `queried_planned`

**Definition:** A question is posed about a future action or plan — e.g. patient asking whether a test/medicine/procedure will be needed.

**Examples:**
- Kya agli baar **test** dobara karna padega?  _(entity: test result)_
- Yeh **dawai** kab tak leni hogi?  _(entity: medication)_
- Kya mujhe **operation** karwana padega future mein?  _(entity: diagnosis/procedure)_

**Decision rule:** Question marker combined with a future/plan marker. Frequently patient-initiated (asking the doctor about next steps).

---

## 3. Combinations that are rare or degenerate — and why we still keep them

None of the 12 combinations are logically impossible, but two are rare enough in real OPD speech that
annotators need explicit guidance rather than an exclusion rule:

- **`negated_planned`** is rare because OPD dialogue mostly plans forward ("karo") rather than
  pre-emptively negating a plan. It occurs almost exclusively when a doctor rules out a future
  intervention ("abhi operation ki zaroorat nahi") or a patient declines a suggested plan. Annotators
  must distinguish it from `negated_current` applied to an ongoing plan being stopped now (e.g., "ab
  yeh dawai band kar do" = stopping a current med → `negated_current` on the medication fact, not
  `negated_planned`, because the state being negated is the present continuation, not a future one).
- **`queried_historical`** and **`queried_planned`** are less frequent than `queried_current` because
  doctors ask about present symptoms far more than about past history or future plans in a single
  short OPD visit, but both occur routinely in structured history-taking ("pehle kabhi X hua tha kya?")
  and in patient-initiated planning questions ("agli baar test karna padega kya?"). Kept as first-class
  tags, not merged, because the extractor must not silently drop or mis-time a doctor's history-taking
  question.

**Explicit gap flag:** these rarity claims are based on general clinical-communication literature and
the Lipi team's operational experience with the pipeline's current failure logs, not a frequency count
over Indian OPD Hinglish transcripts — we do not have a labeled real-transcript corpus to compute base
rates from. The synthetic test set below intentionally over-samples the rare combinations (~16-17
per combination, uniform) rather than mirroring true OPD frequency, precisely so weak performance on
rare-but-important categories (e.g., `negated_planned`) is not masked by their rarity.

---

## 4. Hinglish signal lists

These lists seed both the annotation guideline and the rule-based baseline in Step 4. They are compiled
from the literature-derived trigger classes (NegEx negation triggers, ConText historical/hypothetical
triggers) mapped onto Hindi/Hinglish equivalents, plus additions identified from OPD-style example
sentences. They are a starting point, not a validated exhaustive list — see `hinglish_nlp_gaps.md` for
where they are known to be incomplete.

| Category | Signals |
|---|---|
| Temporal – historical | pehle, pahle, pehle se, purana, purani, ab se pehle, previously, was, had, used to, hua tha, thi/tha (past copula), kabhi (in past-tense clauses), do saal pehle, last month/week/year |
| Temporal – current | abhi, aaj kal, filhaal, currently, is waqt, ab (non-contrastive), hai/hain (present copula), chal raha hai, ho raha hai |
| Temporal – planned | karwa lo, karna hai, karna padega, will, agle hafte, next time, agli baar, aage, kal se (future-oriented), shuru karna hai |
| Negation | nahi, nahin, no, not, nahi tha, nahi hai, denied, absent, without, bilkul nahi, kabhi nahi, band kar diya |
| Uncertainty | shayad, lagta hai, maybe, possibly, thoda, slightly, laga, feel ho raha hai, ho sakta hai, pata nahi, yaad nahi |
| Query | kya, kya...?, "?" marker, kitna, kab tak, kya...hoga/padega, transcription rising-intonation tag |

**Priority order used by the rule-based baseline** (highest wins when multiple signal classes are found
in-window): `negation > query > uncertainty > (temporal signal, else default current)`. This mirrors
ConText's own precedence — Negation is resolved before Temporality — and reflects that in our failure
logs negation loss is the costlier error (a negated fact wrongly recorded as affirmed) compared to a
temporal mis-tag.

---

## 5. Hard cases (20)

**1.** "Pehle sugar high tha, ab control mein hai." _(entity: sugar/diabetes)_
- **Gold:** affirmed_historical (clause 1) + affirmed_current (clause 2)
- **Rationale:** Classic temporal-shift-within-one-sentence case. The entity appears twice with two different temporal states joined by a contrastive 'ab'; a single-label extractor will pick one and silently drop the other fact.

**2.** "Dard nahi hai ab, lekin kal raat bahut tha." _(entity: pain)_
- **Gold:** negated_current (clause 1) + affirmed_historical (clause 2)
- **Rationale:** Negation scoped to 'ab' only; the second clause re-affirms the same entity for last night. A fixed-window negation scanner risks extending 'nahi' scope across the 'lekin' boundary into the historical clause.

**3.** "Purana BP problem nahi thi, par pichle mahine se thoda high aa raha hai." _(entity: BP)_
- **Gold:** negated_historical (clause 1) + uncertain_current (clause 2, 'thoda')
- **Rationale:** Negated historical fact followed immediately by a hedged current onset — 'thoda' signals uncertainty even though the copula is present tense; risk of collapsing to a single affirmed_current tag.

**4.** "Shayad pehle bhi yeh problem thi, par confirm nahi hai." _(entity: diagnosis)_
- **Gold:** uncertain_historical
- **Rationale:** Two hedge markers stack ('shayad' and 'confirm nahi hai') but neither is a true negation of the fact itself — 'confirm nahi hai' negates certainty, not existence. Must not be tagged negated_historical.

**5.** "Agle hafte sugar test karwa lo, abhi karne ki zaroorat nahi." _(entity: test result)_
- **Gold:** affirmed_planned (clause 1) + negated_current (clause 2)
- **Rationale:** The negation in clause 2 attaches to 'abhi karne' (doing it now), not to the planned test itself — the test is still planned, just not immediate. Confusing this with negated_planned would wrongly cancel a valid plan.

**6.** "Kya pehle kabhi TB hua tha?" _(entity: tuberculosis)_
- **Gold:** queried_historical
- **Rationale:** History-taking question; must not default to affirmed_historical just because 'hua tha' (a historical marker) is present — 'kya' converts the whole clause to a query.

**7.** "Weight thoda badh gaya lagta hai is mahine." _(entity: weight)_
- **Gold:** uncertain_current
- **Rationale:** 'Is mahine' (this month) could be misread as historical, but the fact is about the present state (current weight), described with hedge language about a recent change; entity's temporal reference is current, not historical — the time phrase describes the trend period, not when the fact held.

**8.** "Pehle allergy nahi thi kisi cheez se, ab dust se ho rahi hai." _(entity: allergy)_
- **Gold:** negated_historical (clause 1) + affirmed_current (clause 2)
- **Rationale:** Negated historical fact followed by a newly affirmed current fact for the same entity type — must be split into two records, not merged or overwritten.

**9.** "Ho sakta hai agli baar dawai badalni pade." _(entity: medication)_
- **Gold:** uncertain_planned
- **Rationale:** Modal 'ho sakta hai...pade' is a combined uncertainty+plan marker with no explicit temporal keyword like 'agle hafte'; 'agli baar' (next time) alone carries the planned signal.

**10.** "Bukhar abhi nahi hai, par raat ko aata hai." _(entity: fever)_
- **Gold:** negated_current (clause 1) + affirmed_current (clause 2, recurring pattern)
- **Rationale:** Recurring/intermittent symptom pattern: absent right now but a general current pattern is affirmed ('aata hai' = habitual present, not future). Both are 'current' temporally but opposite epistemic states for the same moment-type description.

**11.** "Operation ki zaroorat abhi nahi hai, next visit mein dekhenge." _(entity: diagnosis/procedure)_
- **Gold:** negated_planned
- **Rationale:** True negated_planned case: the plan itself (operation) is being explicitly ruled out for now, with re-evaluation deferred to next visit — distinguish from negated_current, since no operation was ever underway to 'stop'.

**12.** "Sugar test kal hua tha, abhi tak report nahi aayi." _(entity: test result)_
- **Gold:** affirmed_historical (the test event) + negated_current (the report)
- **Rationale:** Two different sub-facts sharing one entity label ('test result'): the test itself is historical-affirmed, but the report's availability is negated_current. Naive single-tag extraction merges these into one wrong state.

**13.** "Kya abhi bhi khansi hai ya theek ho gayi?" _(entity: cough)_
- **Gold:** queried_current
- **Rationale:** Compound question offering two possible current states (present vs. resolved) — still a single queried_current tag on the target entity; the disjunction should not be split into affirmed/negated variants since neither is asserted.

**14.** "Maine suna hai ki BP high tha uska, pata nahi confirm hai ya nahi." _(entity: BP)_
- **Gold:** uncertain_historical
- **Rationale:** Reported/hearsay speech ('maine suna hai') about another time point, explicitly flagged as unconfirmed ('pata nahi confirm hai ya nahi') — hearsay + explicit non-confirmation both point to uncertain, not affirmed, despite 'tha' being a strong historical marker.

**15.** "Filhaal koi dawai nahi le rahe hain sugar ke liye." _(entity: medication)_
- **Gold:** negated_current
- **Rationale:** 'Filhaal' (currently) + 'nahi le rahe' negates an ongoing action; must not be read as negated_historical despite absence of an explicit 'abhi' — 'filhaal' is the current-signal doing that work.

**16.** "Pehle se hi thoda weakness tha, ab bhi hai." _(entity: weakness)_
- **Gold:** affirmed_historical (clause 1) + affirmed_current (clause 2, continuity)
- **Rationale:** 'Pehle se hi' + 'ab bhi' explicitly asserts continuity from past into present — the correct extraction is a historical fact continuing into the present, best represented as two linked facts (historical AND current), not collapsed into one and not treated as contradictory.

**17.** "Agar bukhar dobara aaya to dawai le lena." _(entity: fever)_
- **Gold:** uncertain_planned (conditional instruction)
- **Rationale:** Conditional 'agar...to' framing is neither a firm plan nor a query — it is a contingent future instruction, closest to uncertain_planned; do not tag as affirmed_planned since the fever recurrence itself is not asserted, only conditionally anticipated.

**18.** "Nausea ho raha hai kya abhi, ya sirf chakkar aa rahe hain?" _(entity: nausea)_
- **Gold:** queried_current
- **Rationale:** Doctor differentiating between two possible current symptoms in one question; only the named target entity ('nausea') is tagged as queried_current — the alternative symptom mentioned ('chakkar') is a separate entity requiring its own tag, not part of this one's rationale.

**19.** "Purani body pain ki history hai, par abhi kam hai." _(entity: pain)_
- **Gold:** affirmed_historical (clause 1) + uncertain_current (clause 2, 'kam hai' downgraded severity, not full negation)
- **Rationale:** 'Kam hai' (is less) is a severity downgrade, not a negation — the pain still exists currently at reduced intensity, so negated_current is wrong; treat as affirmed_current or uncertain_current per severity-vs-existence distinction, here uncertain_current chosen because 'kam' introduces ambiguity about clinical significance.

**20.** "Test abhi karna hai ya agli visit pe karwayein?" _(entity: test result)_
- **Gold:** queried_planned
- **Rationale:** Question offers two future-timing options for the same planned action — both options are planned, and the uncertainty is about timing/query, not about whether the test will happen at all, so the correct tag is queried_planned rather than uncertain_planned.

---

## 6. Inter-annotator agreement (IAA) protocol

Modeled on the ConText study's finding that reported kappa was depressed mainly by annotation-process
drift (a long gap between training and the second annotation batch), not task difficulty itself
(Harkema et al. 2009) — our protocol is designed to prevent that failure mode directly, plus the
i2b2 finding that rare categories (their `conditional`) are where independent annotators diverge most.

1. **Independent double-annotation.** Both annotators tag epistemic and temporal axes independently,
   as two separate columns, never as one combined 12-way label — this prevents one axis's disagreement
   from being hidden inside a compound-label mismatch and lets us compute per-axis kappa (Cohen's kappa
   per Harkema et al. 2009, §3.3).
2. **No batching gap.** All annotation happens in a single sitting per batch of ≤50 sentences, with a
   5-minute guideline re-read before each batch — directly addressing the ConText paper's diagnosis
   that a "significant time lapse" between training and annotation degraded their second annotator's
   guideline recall.
3. **Disagreement resolution, axis-independent:**
   - If annotators agree on epistemic but disagree on temporal (or vice versa): the agreed axis is
     locked; the disputed axis goes to a third adjudicator (a clinician on the Lipi team) who sees only
     the disputed axis and the sentence, not either annotator's label, to avoid anchoring bias.
   - If annotators disagree on **both** axes: treat as a hard case candidate — route to a group review
     with both annotators and the adjudicator present, and add the resolved sentence (with rationale)
     to the hard-cases bank (§5) regardless of outcome, since a full double-disagreement is evidence the
     guideline itself is ambiguous for that pattern.
   - Multi-clause sentences (entity appearing twice with different temporal/epistemic states, per §5
     hard cases) are annotated as multiple fact-records from the start, never merged into one label —
     annotators mark clause boundaries before assigning tags.
4. **Rare-category floor.** Following the i2b2 finding that `conditional` (their rarest category) had
   the lowest cross-system overlap, we track agreement separately for the two rarest tags
   (`negated_planned`, `queried_historical`) and require a minimum of 15 doubly-annotated examples of
   each before trusting the computed kappa for that tag — below that count, kappa is reported but
   flagged as low-confidence rather than acted upon.
5. **Report both raw and specific agreement.** Following Harkema et al.'s use of positive/negative
   specific agreement alongside Cohen's kappa (their Table 6) — because high raw agreement is often
   driven by the frequent default case (`affirmed_current`) — we will report PSA (agreement on
   non-default tags) separately per axis, not just overall kappa, to avoid a misleadingly high headline
   number.

**Gap flag:** this protocol has not yet been run with real annotators on real transcripts; it is a
design specification derived from documented failure modes in the cited literature, pending a pilot
with the Lipi clinical team.
