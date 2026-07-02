# API Costs

## Purpose

Track Lipi's cost per consultation. Do not rely on stale vendor prices. Add source links, dates, and assumptions whenever a real price is entered.

## Cost Doctrine

- Cost per consultation is a product metric, not just an engineering metric.
- Sarvam plain STT is the default ASR cost.
- Gemini formatting is optional and must be tracked separately.
- Diarization cost is included only when used.
- Do not train ASR before market proof.

## Per-Consultation Cost Formula

```text
total_cost_per_consultation =
  asr_cost
  + optional_diarization_cost
  + optional_gemini_formatting_cost
  + messaging_cost
  + storage_cost
  + infrastructure_cost
  + observability_cost
```

## Cost Ledger Template

| Date | Clinic | Consultations | Avg audio min | ASR mode | Diarization | Gemini formatting | Messaging | Total vendor cost | Cost/consult | Notes |
| --- | --- | ---: | ---: | --- | --- | --- | --- | ---: | ---: | --- |
| YYYY-MM-DD | TBD | 0 | 0 | Sarvam plain STT | No | No | No | 0 | 0 | Initialize when real usage begins |

## Vendor Assumptions

### Sarvam STT

Default use:
- Plain speech-to-text

Track:
- Price unit
- Audio minutes
- Billing rounding
- Language impact
- Failure retries
- Free credits or committed-use discounts

Source:
- Vendor pricing URL:
- Verified date:
- Notes:

### Diarization

Default use:
- Off

Use only when:
- Real consultation evidence shows speaker separation is necessary.
- The clinical review workflow cannot solve the issue more cheaply.

Track:
- Added cost per audio minute
- Accuracy improvement
- Review-time reduction
- Error reduction

Source:
- Vendor pricing URL:
- Verified date:
- Notes:

### Gemini Formatting

Default use:
- Optional formatting only

Allowed:
- Formatting reviewed structured facts into readable note text.

Not allowed:
- Creating clinical facts
- Inferring diagnoses
- Resolving conflicts
- Adding unsupported plan items

Track:
- Model
- Input tokens
- Output tokens
- Calls per consultation
- Cost per formatting call

Source:
- Vendor pricing URL:
- Verified date:
- Notes:

### WhatsApp Or Messaging

Track:
- Provider
- Message type
- Template category
- Country
- Cost per sent message
- Failed sends and retries

Source:
- Vendor pricing URL:
- Verified date:
- Notes:

### Infrastructure

Track:
- App hosting
- Database
- Storage
- Logs and monitoring
- Backup cost
- Monthly fixed cost allocated over consultations

## Cost Review Cadence

Update weekly during pilots:
- Consultations processed
- Vendor spend
- Cost per consultation
- Main cost driver
- Any unexpected retries or failures
- Margin at target pricing

## Red Flags

- Diarization becomes default before evidence supports it.
- Gemini is used for fact creation.
- ASR retries silently double cost.
- Messaging cost is ignored in pricing.
- Infrastructure fixed cost is not allocated across low-volume pilots.

## Related Notes

- [[03_PRODUCT_STRATEGY]]
- [[05_VALIDATION_PLAN]]
- [[07_DECISIONS]]
