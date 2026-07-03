export type BlogSection = {
  heading: string;
  body: string;
  image?: { src: string; alt: string; caption: string };
};

export type ResearchPost = {
  slug: string;
  tag: string;
  title: string;
  intro: string;
  heroStat?: { value: string; label: string; sublabel: string };
  pullQuote?: { text: string; afterSection: number };
  sections: BlogSection[];
  keyFindings: string[];
};

export const RESEARCH_POSTS: ResearchPost[] = [
  {
    slug: 'drug-safety-indian-formularies',
    tag: 'Dataset complete',
    title: 'Drug safety for Indian formularies',
    intro:
      'Most drug interaction databases were built on studies from European and North American populations. They miss two things that matter in Indian OPD: the brand-name combinations that confuse Indian prescribers, and the allele frequencies that determine how individual patients actually metabolize common drugs.',
    pullQuote: {
      text: 'Eight of those 15 rules are deployable in OPD settings today without genomic testing — they flag elevated population-level risk from clinical signals the doctor already has.',
      afterSection: 1,
    },
    sections: [
      {
        heading: 'The gap in existing databases',
        body: 'Global interaction checkers like Micromedex and the BNF were built on adverse event data and clinical trials that are heavily weighted toward Western populations. This creates two blind spots in the Indian prescribing context: first, the brand-name landscape is entirely different (a drug sold under three different names by three different manufacturers in India will not map cleanly to a single entry in a US-centric database); second, the pharmacogenomic risk profiles used to flag dangerous combinations assume European-ancestry allele frequencies that do not hold for South Asian patients.',
      },
      {
        heading: 'The interaction dataset',
        body: "We started with 182 candidate drug-drug interaction pairs identified across three independent sources: openFDA adverse event reports, PubMed clinical studies, and India's National List of Essential Medicines. Each candidate was cross-verified against all three sources; 33 pairs were rejected where the evidence did not hold across sources. The remaining 80 pairs carry explicit severity ratings (major, moderate, minor), mechanism descriptions, and clinical management notes grounded in primary literature - not copied from a single aggregated database.",
      },
      {
        heading: 'Pharmacogenomics without a genomics lab',
        body: 'Standard pharmacogenomic references like CPIC were built on predominantly European allele frequencies. The key metabolic genes for common OPD drugs - CYP2C19 for clopidogrel and PPIs, CYP2D6 for codeine and tramadol, CYP2C9 for warfarin and NSAIDs - have meaningfully different variant distributions in South Asian populations. We built 15 gene-drug rules using Indian population allele frequencies from IndiGen (N=1,029 whole genomes, 2020) and GenomeIndia (N=9,768 samples across 83 population groups, 2024). Eight of those 15 rules are deployable in OPD settings today without genomic testing - they flag elevated population-level risk from clinical signals the doctor already has: age, sex, concurrent medications, and organ function markers in the vitals.',
      },
      {
        heading: 'What deploys now vs. what comes next',
        body: "The 8 deployable-today PGx rules are structured as decision-support flags, not diagnostic conclusions. When a doctor prescribes clopidogrel to a patient of South Asian ancestry, the system flags that CYP2C19 loss-of-function variants are significantly more prevalent in this population than CPIC's European-derived baselines assume, and that the clinical evidence for alternative antiplatelet therapy is stronger than the default protocol reflects. The doctor decides. The remaining 7 rules require either genomic confirmation or a more complete clinical picture than OPD data typically provides - those are staged for Phase 2 integration.",
      },
    ],
    keyFindings: [
      '80 DDI pairs verified across openFDA, PubMed, and NLEM - 33 candidates rejected after cross-source verification',
      '15 PGx rules grounded in IndiGen and GenomeIndia South Asian allele frequency data',
      '8 rules deployable today without genomic testing - flag population-level risk from existing clinical signals',
      'Key genes: CYP2C19, CYP2D6, CYP2C9 - all with documented South Asian allele frequency gaps vs. CPIC European defaults',
      'Severity-rated and mechanism-described: every pair is actionable, not just flagged',
    ],
  },
  {
    slug: 'amr-surveillance-gap',
    tag: 'Analysis complete',
    title: "India's primary-care AMR surveillance gap",
    intro:
      "India carries one of the highest antimicrobial resistance burdens in the world. The surveillance infrastructure meant to track it has a structural blindspot: it sees hospital data almost exclusively, and hospital data represents a small fraction of where antibiotics are actually prescribed.",
    heroStat: {
      value: '80 pp',
      label: 'Primary-care surveillance gap',
      sublabel:
        '~80% of antibiotic consumption happens in primary care. 0% of ICMR AMRSN and NCDC NARS-Net specimens come from primary-care settings.',
    },
    pullQuote: {
      text: 'In 12 site-years examined, 0% of specimens came from primary-care settings. The surveillance network has grown — but never toward primary care.',
      afterSection: 0,
    },
    sections: [
      {
        heading: 'Where the gap was measured',
        body: "ICMR's Antimicrobial Resistance Surveillance Network (AMRSN) and NCDC's NARS-Net are India's two flagship AMR surveillance networks. We reviewed 12 site-years of primary-source data from both - ICMR AMRSN across 2019-2023 (21-29 sentinel hospitals per year) and NCDC NARS-Net across 2017-2024 (13-54 sites per year). Both networks state explicitly in their own reports that all sentinel sites are tertiary-care hospitals or medical colleges. In 12 site-years examined, 0% of specimens came from primary-care or community settings.",
        image: {
          src: '/research/chart1_consumption_vs_surveillance.png',
          alt: 'Bar chart comparing antibiotic consumption in primary care vs. surveillance coverage',
          caption:
            'Where antibiotics are consumed vs. where surveillance samples are collected. The surveillance network sees the right side of this chart almost exclusively.',
        },
      },
      {
        heading: 'How big the gap is',
        body: "Roughly 80% of India's antibiotic consumption happens in primary care and community settings - corroborated by four independent consumption-side proxies: direct community-use citation (Kotwani and Holloway, BMC Infect Dis 2011), retail-channel sales data (PharmaTrac, in Koya et al., Lancet Reg Health SEA 2022), outpatient-share data from single-facility studies, and private-vs.-public prescription share estimates. The surveillance-side figure (0%) is an exact count with no uncertainty, confirmed across every site-year examined. The uncertainty range for the consumption-side estimate is 65-87.5 pp, reflecting the spread across four non-equivalent proxies - not a statistical confidence interval.",
        image: {
          src: '/research/chart2_sentinel_site_timeseries.png',
          alt: 'Line chart showing sentinel site count over time for ICMR AMRSN and NCDC NARS-Net',
          caption:
            'Sentinel site count over time across ICMR AMRSN and NCDC NARS-Net. The network has grown significantly - but expansion has never moved toward primary-care settings.',
        },
      },
      {
        heading: 'The geographic blindspot',
        body: "Coverage is concentrated in a small number of urban tertiary centers. State-level primary-care prescribing - the majority of actual antibiotic use across India - has no representation in either network. The result is a surveillance system that is structurally incapable of detecting resistance signals where they emerge earliest: at the point of first antibiotic contact.",
        image: {
          src: '/research/chart3_state_blindspot_scatter.png',
          alt: 'Scatter plot showing state-level surveillance site density vs. population',
          caption:
            "State-level surveillance site density vs. population. Most of India's population is in states with sparse or zero primary-care AMR representation.",
        },
      },
      {
        heading: 'What Lipi data could reveal',
        body: "Lipi's doctor-confirmed OPD prescribing data sits exactly where national AMR surveillance has no visibility - at the point of care where roughly four in five Indian antibiotic courses are prescribed. As decision support, a validated escalation-rate signal from Lipi's prescription and follow-up outcome data could give prescribers and public-health partners an early read on local resistance pressure that today's hospital-only networks structurally cannot provide until months later. This positioning is a hypothesis pending validation. Lipi's current data streams are prescriptions, diagnoses, and follow-up outcomes - not microbiology culture results. Validation against real AMRSN and NARS-Net resistance data is required before this signal can be presented as established, and a validation study protocol has been designed to do exactly that.",
      },
    ],
    keyFindings: [
      '80 percentage-point gap between primary-care antibiotic consumption share (~80%) and primary-care surveillance representation (0%)',
      '12 site-years of ICMR AMRSN and NCDC NARS-Net primary-source reports reviewed',
      '0% primary-care specimens in either network - confirmed exact count, not an estimate',
      'Uncertainty range 65-87.5 pp across four independent consumption-side proxies',
      'Validation study protocol designed: escalation-rate signal vs. AMRSN and NARS-Net resistance data',
    ],
  },
  {
    slug: 'hinglish-clinical-nlp',
    tag: 'Benchmark complete',
    title: 'Hinglish clinical NLP',
    intro:
      'Indian OPD doctors switch between Hindi and English mid-sentence, mid-word, and mid-thought. Clinical NLP tools built for English - NegEx, ConText, most BERT-based models - were not designed for this and fail on patterns that appear in nearly every Indian consultation transcript.',
    pullQuote: {
      text: 'Clause-splitting before classification eliminates cross-clause signal leakage and unblocks three other failure modes as a side effect.',
      afterSection: 1,
    },
    sections: [
      {
        heading: 'Why existing tools fail',
        body: "NegEx and ConText, the two most widely deployed rule-based clinical NLP systems for negation and temporality detection, were designed and evaluated on English clinical notes from US health systems. The core mechanism - a fixed token window around an entity mention, searched for signal words from a hand-curated list - works for English because English negation and temporal markers are relatively predictable in clinical note style. In transcribed Hinglish dialogue, the same mechanism breaks in at least six distinct ways that do not arise in English at all.",
      },
      {
        heading: 'The benchmark we built',
        body: 'No published benchmark existed for negation and temporality detection in transcribed Hindi-English code-switched medical dialogue. We designed a 12-way annotation scheme covering four epistemic states (affirmed, negated, uncertain, queried) crossed with three temporal dimensions (current, historical, planned), then generated a 200-sentence synthetic test set with coverage across epistemic-temporal combinations and Hinglish pattern categories. A rule-based NegEx/ConText-style baseline achieved 85.2% macro-F1 against a 1.3% do-nothing baseline - better than expected, but with 29 specific errors that map to 6 failure modes, each with a deterministic engineering fix.',
      },
      {
        heading: 'The six failure modes',
        body: "The 29 baseline errors break into six distinct classes. The largest by count is missing planned-temporal signals (28% of errors): Hinglish modal-future forms like 'hogi/hoga/padega' and deferral phrases like 'kab tak' are absent from the baseline's temporal signal list, causing planned actions to be classified as current. The second largest is hedge-negation conflation (24%): 'pata nahi' (don't know) triggers the negation classifier because it contains 'nahi', but the phrase negates the speaker's knowledge, not the clinical fact - structurally identical to the English hedge-phrase problem documented in ConText's own error analysis. The structurally most critical failure (17% of errors by count, highest real-world risk) is multi-clause window bleed: a fixed +-5-token window bleeds across clause boundaries in multi-clause sentences, exactly the pattern doctors use to describe symptom resolution. The remaining three modes are substring false positives (the substring 'no' fires inside the word 'normal'), missing idiom triggers ('control mein hai' not recognized as negation-equivalent), and negated-planned collapsing to negated-current.",
      },
      {
        heading: 'The fix priority order',
        body: "Clause-splitting before classification is the highest-priority fix. Using Hinglish contrastive conjunctions ('par', 'lekin', 'ab', 'phir') as clause boundaries and scoring each clause independently eliminates cross-clause signal leakage and unblocks three other failure modes as a side effect. Word-boundary tokenization (replacing raw substring matching) is a one-line fix with no design trade-offs and should be applied immediately. Signal-list extensions for planned-temporal markers, uncertainty-suppressing lookup tables for hedge phrases, and idiom-level negation triggers are layered on top. All fixes are deterministic - no model training required.",
      },
    ],
    keyFindings: [
      '85.2% macro-F1 on a 200-sentence Hinglish clinical NLP benchmark - vs. 1.3% do-nothing baseline',
      '6 failure modes mapped with deterministic engineering fixes - no model training required',
      'Largest failure mode: missing planned-temporal signals (28% of errors) - "hogi/hoga", "kab tak" not in signal list',
      'Most critical fix: clause-splitting before classification - structural change that unblocks 3 other failure modes as a side effect',
      'No published Hinglish clinical NLP benchmark existed before this work',
      'All 6 fixes are rule-based and layerable; highest-priority fix eliminates cross-clause leakage structurally',
    ],
  },
  {
    slug: 'indian-opd-ontology',
    tag: 'Ontology complete',
    title: 'Indian OPD clinical ontology',
    intro:
      "ICD-10 codes are the standard structure for clinical diagnosis data - but ICD-10 assumes documentation in English by a clinician using Western diagnostic terminology. Indian OPD practice does not work this way. Patients present with 'sugar', 'BP', 'bukhar', 'kamar dard'. Doctors chart in Hinglish. A clinical NLP system that can only match English ICD-10 names will miss most of what is actually said.",
    pullQuote: {
      text: "After 20+ PubMed searches, we found no published Hindi-English clinical vernacular glossary. The vocabulary Indian OPD doctors and patients use has not been documented anywhere.",
      afterSection: 1,
    },
    sections: [
      {
        heading: 'What we built',
        body: "150 top Indian OPD diagnoses, ranked by a composite score derived from GBD 2016 India burden data (Lancet, ICMR/PHFI/IHME collaboration), NFHS-5 prevalence data, and 7 published Indian OPD morbidity studies. Each entry is mapped to both ICD-10-CM and ICD-10-WHO codes - 35% of entries diverge between the two coding systems, and divergences with clinical significance (TB confirmation status, stroke laterality, self-harm coding) are flagged explicitly. The top 50 entries carry Hinglish vernacular lookup terms: the words patients and doctors actually use in the clinic, from standard Hindi medical terms (bukhar, khoon ki kami, dil ki bimari) to the English-Hindi hybrids that dominate real OPD speech (sugar, BP, loose motion, gas trouble).",
      },
      {
        heading: 'The most important gap we found',
        body: "After 20+ PubMed searches covering health literacy, lay illness vocabulary, Hindi medical terminology, culture-bound syndrome glossaries, and clinical NLP corpora, we found no published Hindi-English clinical vernacular glossary that could serve as a ground-truth source for these lookup terms. Zero of the 50 Hinglish-name entries could be sourced to published literature. All 50 are labeled 'inferred' - derived from clinical knowledge, not validated by a published corpus. This is a finding about the state of the literature, not a shortcut: the vocabulary that Indian OPD doctors and patients actually use has not been systematically documented in any resource we could locate. Lipi's own doctor-confirmed transcript corpus is the most direct path to filling this gap - every confirmed diagnosis label from a real consultation is a validated Hinglish term the literature has never catalogued.",
      },
      {
        heading: 'Why the ontology matters for extraction',
        body: "A clinical NLP system extracting diagnoses from Hinglish transcripts needs to recognize 'sugar' as mapping to diabetes mellitus (E11.x), 'BP' as hypertension (I10), and 'kamar dard' as a candidate for lumbago, musculoskeletal pain, or referred visceral pain depending on accompanying symptoms. Without a lookup table that maps vernacular terms to ICD codes, the extractor either misses the diagnosis entirely or falls back on English-only pattern matching. The 150-entry ontology with 435 lookup terms gives the extractor the vocabulary to recognize what Indian doctors actually say, not just what a Western clinical NLP corpus trained on.",
      },
      {
        heading: 'Data discipline and honest gaps',
        body: "Only 21% of burden scores are cited to a real India-specific source (GBD 2016 India data, NFHS-5 prevalence, or published OPD morbidity literature). The remaining 79% are labeled explicitly as 'clinical-knowledge placeholder - NOT a sourced number'. The OPD manageability scores are documented as single-analyst clinical judgment, not adjudicated by a physician panel. The file is a recognition-priority ordering for an NLP system - not a validated epidemiological ranking - and that distinction is stated plainly in every entry that uses a placeholder rather than presenting early estimates as measured data.",
      },
    ],
    keyFindings: [
      '150 diagnoses, 435 lookup terms, ICD-10-CM and ICD-10-WHO coded',
      '35% of entries have divergent ICD-10-CM vs. ICD-10-WHO codes - flagged where clinically significant',
      '0 Hinglish vernacular entries sourced to published literature - no such glossary was found to exist',
      '79% of burden scores explicitly labeled as clinical-knowledge placeholders, not sourced numbers',
      "Lipi's own transcript corpus is the novel source needed to validate all 50 Hinglish-name entries",
    ],
  },
];
