# Tokenomics

Source: aggregate records in `pilot.db`; no records are fabricated.

## Measured averages by run type

### plan

```json
{
  "input_tokens": 17849.4,
  "cached_input_tokens": 7485.0,
  "output_tokens": 4632.8,
  "cost_usd": 0.00428846,
  "provider_cost_usd": 0.00366601,
  "duration_ms": 36416.6
}
```

### answer_sheet_reading

```json
{
  "input_tokens": 22536.75,
  "cached_input_tokens": 0.0,
  "output_tokens": 3716.0,
  "cost_usd": 0.00411167,
  "provider_cost_usd": 0.00411167,
  "duration_ms": 37111.75
}
```

### next_steps

```json
{
  "input_tokens": 11077.5,
  "cached_input_tokens": 5213.5,
  "output_tokens": 1302.25,
  "cost_usd": 0.00188921,
  "provider_cost_usd": 0.00142209,
  "duration_ms": 14073.25
}
```

### worksheets

```json
{
  "input_tokens": 4124.0,
  "cached_input_tokens": 1380.0,
  "output_tokens": 675.0,
  "cost_usd": 0.0007844,
  "provider_cost_usd": 0.000688,
  "duration_ms": 6207.0
}
```

## Agent totals

```json
{
  "lesson_planner": {
    "calls": 5,
    "input_tokens": 17097,
    "cached_input_tokens": 6329,
    "output_tokens": 11881,
    "cost_usd": 0.00780842,
    "duration_ms": 86718,
    "cost_share": 0.16890276
  },
  "check_builder": {
    "calls": 4,
    "input_tokens": 21527,
    "cached_input_tokens": 7926,
    "output_tokens": 3883,
    "cost_usd": 0.00429235,
    "duration_ms": 29308,
    "cost_share": 0.09284718
  },
  "reviewer": {
    "calls": 8,
    "input_tokens": 48536,
    "cached_input_tokens": 22526,
    "output_tokens": 2952,
    "cost_usd": 0.00689275,
    "duration_ms": 39632,
    "cost_share": 0.14909604
  },
  "answer_sheet_reader": {
    "calls": 156,
    "input_tokens": 90147,
    "cached_input_tokens": 0,
    "output_tokens": 14864,
    "cost_usd": 0.0164467,
    "duration_ms": 148447,
    "cost_share": 0.35575609
  },
  "lesson_planner_revision": {
    "calls": 2,
    "input_tokens": 7813,
    "cached_input_tokens": 3012,
    "output_tokens": 4499,
    "cost_usd": 0.0031061,
    "duration_ms": 30284,
    "cost_share": 0.06718758
  },
  "reviewer_revision": {
    "calls": 2,
    "input_tokens": 14687,
    "cached_input_tokens": 6905,
    "output_tokens": 1392,
    "cost_usd": 0.00233732,
    "duration_ms": 13710,
    "cost_share": 0.05055822
  },
  "coach": {
    "calls": 4,
    "input_tokens": 23897,
    "cached_input_tokens": 11581,
    "output_tokens": 3766,
    "cost_usd": 0.00456223,
    "duration_ms": 38724,
    "cost_share": 0.09868491
  },
  "resource_builder": {
    "calls": 1,
    "input_tokens": 4124,
    "cached_input_tokens": 1380,
    "output_tokens": 675,
    "cost_usd": 0.0007844,
    "duration_ms": 6207,
    "cost_share": 0.01696724
  }
}
```

## Projection assumptions

Arithmetic scenarios use 22 school days/month and 1, 2, or 4 full loops/day. They are scenarios, not claims about teacher usage.

## Not measured in the pilot database

- LLM-vs-code diagnosis accuracy/cost experiment.
- Before/after severity-based revision comparison.
- Hosting price.
