# Common Missing Questions

These are the most frequently missing pieces of information when a clinical coding task is submitted. The clarification engine should check for these proactively.

## Big N (Denominator)

- What defines "N" for each treatment column? (randomized? treated? completed?)
- Is N pulled from ADSL or a specific flag in the source data?
- Does the table header show N or n?

## Events vs. Subjects

- Is the count based on number of events or number of subjects with at least one event?
- For "subjects with events" — is it unique subjects per preferred term, per SOC, or overall?

## Dose Groups / Treatment Arms

- How many treatment groups? What are the labels?
- Is there a pooled "Total" column?
- Are dose groups defined by planned or actual treatment?

## TEAE (Treatment-Emergent Adverse Events)

- Definition of treatment-emergent: onset after first dose? Worsening of pre-existing?
- What is the risk window? (e.g., 30 days post last dose)
- Are serious AEs (SAEs) separated or included in overall TEAE?

## Time Windows

- On-treatment period definition (first dose to last dose + X days)
- Baseline definition (last non-missing value before first dose? screening? day 1?)
- Follow-up period boundaries

## Output Specifics

- Sort order (by frequency? alphabetical? SOC order?)
- Percentage denominator (column N? row total? overall N?)
- Decimal places and rounding rules
- Missing data representation ("—", "0", blank, "NE")

## Lab Shift Tables

- Which lab parameters? (all? subset from SAP?)
- Shift from baseline or from screening?
- Normal range source (central lab? local? site-specific?)
- Categories: Low/Normal/High or more granular (e.g., CTCAE grades)?

## Disposition Tables

- Which milestones? (screened, randomized, treated, completed, discontinued)
- Reasons for discontinuation — from which CRF page / SDTM domain?
- Is "ongoing" a valid status to show?
