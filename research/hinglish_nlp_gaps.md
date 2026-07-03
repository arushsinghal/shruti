# Hinglish NLP Gaps — Failure-Mode Engineering Spec

**Source:** rule-based (NegEx/ConText-style) baseline evaluated on `synthetic_test_set.json`
(200 sentences, 12 epistemic×temporal combinations). Baseline made **29/200**
errors (14.5% error rate) against a **85.2%**
macro-F1 on the full 12-way tag combination, versus **1.3%**
macro-F1 for the always-predict-affirmed+current "do nothing" baseline.

**Gap flag:** all numbers below are measured on synthetic sentences generated to exercise the
annotation schema, not on real Lipi transcripts. No accuracy claim here should be read as
production performance — this document exists to specify *what the deterministic extractor must
handle* before real Hinglish transcript data is available for validation, not to claim the baseline
is production-ready.

---

## Failure mode 1 — Negated-planned collapses to negated-current ("zaroorat nahi" pattern)

**Frequency:** 7/29 errors (24% of all baseline errors) — the single
largest error bucket.

**Pattern:** Sentences like *"Abhi {X} ki zaroorat nahi hai"* (no need for X right now) or *"Doctor ne
bola abhi {X} karwane ki zaroorat nahi, next visit pe dekhenge"* are gold-labeled `negated_planned`
(a future action is being explicitly ruled out), but the baseline predicts `negated_current` every
time, because "abhi" (a current-signal word) sits directly inside the ±5-token window and the temporal
priority order (historical > planned > current) never sees a planned-signal word — "zaroorat nahi"
itself carries no temporal marker at all; the *only* future-orientation cue is the deferral phrase
"next visit pe dekhenge", which can fall outside the fixed window.

**Engineering fix:** add "ki zaroorat nahi" and "abhi...zaroorat nahi" as a dedicated planned-negation
trigger phrase (not decomposed into separate negation + current-word matches) — this is a NegEx-style
"pseudo-trigger" fix: recognize the whole phrase as a unit rather than scoring its component tokens
independently, exactly as ConText added phrase-level pseudo-triggers like "clinical history" to stop
"history" from firing spuriously (Harkema et al. 2009, §3.4). Extend scope-search for deferral phrases
("next visit", "agli baar") beyond the fixed token window to the full clause/turn boundary.

---

## Failure mode 2 — Hedge-negation conflation ("pata nahi" / "confirm nahi" misread as fact-negation)

**Frequency:** 7/29 errors (24%).

**Pattern:** *"Pata nahi pehle {X} thi ya nahi"* (don't know if X was there before or not) and *"...confirm
nahi kar sakte abhi"* (can't confirm right now) are gold-labeled `uncertain`, but the baseline predicts
`negated` because "nahi" appears in-window and negation is checked before uncertainty in the priority
order. The Hindi phrase "pata nahi" negates the *speaker's knowledge*, not the *clinical fact* — this is
structurally identical to the well-documented English clinical-NLP trap of internally-negated hedge
phrases (ConText's own error analysis flags "afebrile"-type internal negation as a source of confusion;
Harkema et al. 2009, §5.1 discusses annotator disagreement on exactly this class of phrase).

**Engineering fix:** maintain "pata nahi", "yaad nahi", "confirm nahi", and "pakka nahi" as
**uncertainty pseudo-triggers that suppress negation firing** — i.e., when "nahi" appears as part of
one of these fixed hedge phrases, it must not be scored as a negation signal at all, and the
uncertainty tag should take priority regardless of the general priority order. This is a closed,
enumerable list (unlike free-form negation), so a phrase-level lookup table resolves it completely
rather than requiring model-based disambiguation.

---

## Failure mode 3 — Multi-clause window bleed (fixed-window negation crosses clause boundary)

**Frequency:** 5/29 errors (17%), but this is the failure mode most
directly flagged as a top clinical risk in the original request ("Dard nahi hai ab" losing negation) —
its real-world cost is likely far higher than its synthetic-set frequency suggests, since multi-clause
temporal-shift sentences are exactly the pattern doctors use to describe symptom resolution.

**Pattern:** *"Lagta hai {X} abhi hai, par pehle bilkul confirm nahi tha"* (X seems to be there now, but
wasn't confirmed before) is gold-labeled `uncertain_current` for the entity's primary (first-clause)
state, but the fixed ±5-token window pulls in "pehle" and "confirm nahi tha" from the second clause,
flipping the temporal prediction to `historical`. This is precisely the scope problem ConText was built
to fix relative to NegEx's six-token window (Harkema et al. 2009, §3.1.4) — but ConText's own fix
(scope-to-termination-term) assumes English clause markers and section structure that don't exist in
transcribed Hinglish dialogue.

**Engineering fix:** before running window-based classification, split the sentence into clauses at
Hinglish contrastive/sequential conjunctions — "par", "lekin", "ab", "phir" — used exactly as
ConText's "termination terms" (Table 1 in Harkema et al. 2009) but with a Hindi-specific list. Score
each clause independently and emit **multiple fact-records per entity mention** rather than one merged
label, since real OPD speech (per the annotation schema's hard-cases §5) frequently needs two
temporally-distinct facts about the same entity in one utterance. This is a structural pipeline change,
not a signal-list addition — it must happen upstream of tag classification.

---

## Failure mode 4 — Missing/implicit planned signals ("kab tak", modal-only future reference)

**Frequency:** 4+4/29 = 8/29 errors (28%) — the largest
category when combined.

**Pattern (a):** *"{X} kab tak leni hogi?"* (how long do I need to take X for?) is gold-labeled
`queried_planned`, but "kab tak" and "hogi" are absent from the `temporal_planned` signal list, so the
baseline defaults to `current`. **Pattern (b):** *"Next week {X} ke liye appointment fix ho gaya hai,
karna hi hai"* is gold-labeled `affirmed_planned`, but the phrase "ho gaya hai" (a present-perfect
completion marker, referring to the appointment-fixing event, not the clinical fact itself) triggers
the `temporal_current` signal list before "next week" is checked, because both fall in-window and
`temporal_current` happens to list-match first for this template.

**Engineering fix:** (a) add "kab tak", "kitni der", and modal-future forms "hogi/hoga/padega/padegi" to
`temporal_planned`; (b) fix the temporal priority order to check `historical` and `planned` signals
**before** `current`, matching the schema's own stated priority (§4 of `annotation_schema.md`) — the
current baseline implementation checks historical first but effectively lets any `current` match short
circuit before a `planned` match later in the same window is reached, because the window can contain a
"process" completion marker ("ho gaya hai", referring to scheduling) that is lexically identical to a
"state" completion marker (referring to the clinical fact itself). This requires distinguishing
completion-of-scheduling from completion-of-clinical-state, which a flat signal-word list cannot do —
recommend a rule that any deferred-time-reference word (next week/agli baar) occurring anywhere in the
full sentence (not just the ±5 window) overrides an in-window `current` match.

---

## Failure mode 5 — Substring false positives from partial word matches

**Frequency:** 1/29 in this synthetic set, but flagged as a **structural risk that will scale
with real vocabulary** rather than a synthetic-set artifact — the count here is an undercount because
our synthetic templates were not adversarially designed to trigger it.

**Pattern:** *"Is waqt {X} normal se zyada hai, patient ne khud confirm kiya"* (X is more than normal
right now, patient confirmed it themselves) is gold-labeled `affirmed_current`, but the baseline's
negation-token check on `"no"` matches inside the substring "**no**rmal", firing a false `negated`
prediction. This is the direct Hinglish-vocabulary analogue of a documented NegEx/ConText failure class
— pseudo-negation phrases that look like negation but aren't (Chapman et al. 2001 explicitly built a
"pseudo-negation phrases" filter list for exactly this reason; ConText carries its own pseudo-trigger
list per property, e.g. "no increase", "not cause").

**Engineering fix:** all signal-list matching must be done on **word-boundary-tokenized** matches, never
raw substring containment — the current baseline's `signal_in_window` check does substring matching on
joined window text, which is exactly the bug class this failure mode exposes. Additionally, build a
Hinglish-specific pseudo-negation list analogous to NegEx's (e.g., "normal", "no problem" as a fixed
positive idiom, "koi nahi" when meaning "nobody" rather than negating the entity) before this ships
against real transcripts, since Romanized Hindi has many more English-loanword collisions with
negation substrings ("no" appearing inside "normal", "noida", "nose", etc.) than the original English
corpora NegEx/ConText were built on.

---

## Failure mode 6 — Negation lost when the negated state is described periphrastically ("ab control mein hai")

**Frequency:** 1/29 errors (3%) — smallest bucket by count, but flagged separately (not merged into
mode 3) because its mechanism is distinct: this is a missing-signal error, not a window-scope error.

**Pattern:** *"{X} ab control mein hai, koi symptom nahi dikh raha abhi"* (X is under control now, no
symptom visible right now) is gold-labeled `negated_current` — the entity's active clinical presence is
being denied — but the baseline predicts `affirmed_current`, because "control mein hai" contains no
signal word from the `negation` list near the entity token; the actual negation ("nahi") in the sentence
is attached to "symptom" rather than to the target entity's own surface form, and falls outside the
±5-token window anchored on the entity mention.

**Engineering fix:** "X control mein hai" is a common Hinglish idiom for a chronic condition being
managed/resolved and should be added as its own negation-equivalent trigger phrase (parallel to
NegEx's phrase-level triggers, e.g. "ruled out"), rather than relying on a downstream "nahi" token to
be in-window. This is a distinct gap from mode 1 (which fires on an explicit "nahi" that is
mis-scoped) — here no negation token is even adjacent to the entity, so no window-size increase fixes
it; only an idiom-level trigger does.

---

## Summary table

| # | Failure mode | Error count | % of errors | Fix type |
|---|---|---|---|---|
| 1 | negated_planned → negated_current ("zaroorat nahi") | 7 | 24% | Phrase-level pseudo-trigger |
| 2 | Hedge-negation conflation ("pata nahi") | 7 | 24% | Uncertainty-suppresses-negation lookup table |
| 3 | Multi-clause window bleed | 5 | 17% | Clause-splitting before classification (structural) |
| 4 | Missing/implicit planned signals | 8 | 28% | Signal-list extension + priority-order fix |
| 5 | Substring false positives ("no" in "normal") | 1 (undercounted) | 3% | Word-boundary tokenization + pseudo-negation list |
| 6 | Negation lost via periphrastic idiom ("control mein hai") | 1 | 3% | Idiom-level negation trigger |

Total: 7+7+5+8+1+1 = 29, matching the baseline's full error count stated above.

**Recommended engineering priority for the deterministic extractor:** fix #3 (clause splitting) first —
it is structural, addresses the exact production failure case named in the original request ("Dard
nahi hai ab" losing negation across a clause boundary), and unblocks correct behavior for #1 and #2 as
a side effect (once each clause is scored independently, cross-clause signal leakage stops). Then apply
#5 (word-boundary matching) as a correctness floor, since it is a one-line fix with no design
trade-offs. #1, #2, and #4 are then signal-list/lookup-table extensions layered on top.

**What this benchmark does NOT tell us:** these are the failure modes exhibited by a rule-based
baseline on *synthetic, template-generated* sentences designed to test the schema — they are not a
measurement of what breaks on real OPD transcripts, and the frequencies above (which failure mode is
"biggest") may not hold at all on real speech, which will have more disfluency, self-correction,
overlapping speech, and vocabulary variety than any template can anticipate. Real-transcript validation
must be the next research step before any of these fixes are prioritized for the production pipeline.
