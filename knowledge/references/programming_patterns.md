# Programming Patterns

Reusable patterns for clinical programming tasks. These patterns are language-agnostic descriptions; language-specific implementations live in `data/assets/code/`.

## Pattern: Big N Header

Compute the denominator for each treatment column and display in the header.
- Source: ADSL (typically `SAFFL='Y'` or `ITTFL='Y'`).
- Group by: treatment variable (`TRT01AN`, `TRT01A`).
- Display: `Treatment A (N=xxx)`.

## Pattern: Frequency Count with Percentage

Count subjects meeting a criterion and compute percentage against Big N.
- Count: number of unique subjects (`USUBJID`).
- Percentage: `n / N * 100`, formatted to specified decimal places.
- Handle zero denominators: display "0" or "—" per specification.

## Pattern: TEAE Flagging

Identify treatment-emergent adverse events.
- Onset date (`AESTDTC` or `ASTDT`) is on or after first dose date.
- Or: pre-existing condition worsened after first dose.
- Risk window: up to X days after last dose (study-specific).

## Pattern: Shift Table

Compare baseline value category to post-baseline category.
- Categories: Low / Normal / High (or CTCAE grades).
- Baseline: last non-missing pre-dose value.
- Post-baseline: worst post-baseline value or by-visit.
- Display: matrix of baseline (rows) vs. post-baseline (columns).

## Pattern: Disposition Summary

Summarize subject flow through study milestones.
- Milestones: screened → randomized → treated → completed → discontinued.
- Discontinued: break down by primary reason.
- Source: ADSL disposition variables or DS domain.

## Pattern: Sort Order

Standard sort orders for clinical tables:
- AE tables: by SOC (international order), then PT (alphabetical or by frequency).
- Lab tables: by parameter name (alphabetical) or by clinical significance.
- Listings: by subject, then by date/time.
