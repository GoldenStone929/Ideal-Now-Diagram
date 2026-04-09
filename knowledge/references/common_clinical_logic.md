# Common Clinical Logic

Frequently used derivation rules and logic fragments in clinical programming.

## Population Flags

```
Safety population:  SAFFL = 'Y' where subject received ≥1 dose of study drug
ITT population:     ITTFL = 'Y' where subject was randomized
Per-protocol:       PPROTFL = 'Y' where subject completed without major deviations
```

## Treatment-Emergent Logic

```
TEAE if:
  (AE start date ≥ first dose date)
  OR (AE start date < first dose date AND AE worsened after first dose)

AND optionally:
  (AE start date ≤ last dose date + risk_window_days)
```

## Baseline Derivation

```
Baseline value = last non-missing assessment on or before first dose date
If multiple assessments on the dose date: use the pre-dose assessment
If no pre-dose value exists: use screening value (study-specific)
```

## Worst Post-Baseline

```
For lab shift / severity analysis:
  worst_post_baseline = max severity (or min/max value) across all post-baseline records
  Exclude unscheduled visits if specified in SAP
```

## Duration Calculation

```
AE duration (days) = AE end date - AE start date + 1
If AE is ongoing: duration = reference date - AE start date + 1
                   OR flag as "ongoing" per specification
```

## Percentage Formatting

```
If n = 0:           display "0" (not "0.0" or blank, unless specified otherwise)
If n > 0 and < 1%:  display "<1.0" (or "< 1", study-specific)
Otherwise:          display to 1 decimal place (e.g., "45.3")
Denominator = 0:    display "—" or "NE" (not estimable)
```

## Multiple Event Handling

```
For "subjects with ≥1 event": count each subject once regardless of event count
For "number of events": count every event record
For worst severity: take the maximum severity per subject per PT (or per SOC)
```
