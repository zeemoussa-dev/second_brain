---
name: macc-forecast-generator
description: Two-step generation of a real customer's own MACC Forecast Sheet -- stage a working copy plus an info-needed checklist first, then fill it once the real info is actually gathered. Every total, both growth scenarios, both dashboards, and the chart are real Excel formulas already baked into the template, this Skill never computes anything itself.
version: 0.3.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [second-brain, sales, macc, excel, vault-write]
---

# MACC Forecast Generator

Your own real write access to a customer's MACC Forecast Sheet. **Read
`Work/Templates/MACC Forecast Template.md` first** -- it documents the
real, hand-built template this Skill fills (all 6 sheets, the real
cell/table contract, color coding).

## The real design: Excel does the math, you just fill it in

Neither script here calculates a MACC size or a growth projection --
every quarterly total, both growth scenarios (Fixed Rate and Historical
Average), both dashboards, and the chart are real Excel formulas already
in the template (`Work/Templates/MACC Forecast Template.xlsx`).

## Two real steps, not one -- don't interrogate Mahmoud in one message

**Found live, 2026-08-24 (operator: "The Agent Asked for so Many Info in
one go... my Recommendation the Agent should Create a copy of the
template and an md file next to it under the customer and ask me hey I
looked inside our vault I found some info but it's not enough...").**
Asking a long list of questions in one chat message is a real UX
failure. Instead:

### Step 1 -- Stage (do this first, always)

1. Check the customer's real pipeline (`Work/Customers/<Customer>/
   Opportunities/*/*.md`) -- pull whatever real fields already exist
   (`expected_consumption`, `status`, `technologies`).
2. Call `stage_macc_forecast.py` to place a fresh, BLANK working copy of
   the template in the customer's own folder:
   ```
   terminal(command="PYTHONUTF8=1 python \"${HERMES_SKILL_DIR}\scripts\stage_macc_forecast.py\" --customer \"<Customer>\"")
   ```
   Lands at `Work/Customers/<Customer>/Files/MACC Estimator/<Customer>
   MACC Forecast <date> (staged).xlsx`.
3. `write_file` a real, human-readable checklist next to it:
   `Work/Customers/<Customer>/Files/MACC Estimator/<Customer> MACC
   Forecast <date> - Info Needed.md` -- structure it as: what's already
   known (with its real source -- an Opportunity note, or something
   Mahmoud already said), and what's still missing, one item per line,
   easy to fill in by hand. See "Info Needed checklist shape" below.
4. Reply to Mahmoud in ONE short message: name what you already found,
   say plainly you need more, and point at the checklist file's real
   path -- don't ask the missing questions inline in chat too.

### Step 2 -- Fill (once the real info comes back)

5. When Mahmoud confirms the missing info -- either by answering in
   chat, or by telling you he filled in the checklist file (read it back
   with `read_file` in that case) -- gather it into the real payload
   shape and call `fill_macc_template.py`:
   ```json
   {
     "customer": "Adnoc",
     "term_months": 36,
     "forecast_start_quarter": "2026-10-01",
     "last_macc_size_usd": 1500000,
     "last_macc_consumption_end_usd": 40000,
     "last_macc_end_date": "2026-09-30",
     "assumed_qoq_growth_rate": 0.04,
     "growth_history": [
       {"quarter": "2026-Q3", "actual_consumption_usd": 40000}
     ],
     "engagements": [
       {
         "name": "Azure Data Manager for Energy",
         "type": "New Workload",
         "source": "Opportunity: Azure Data Manager for Energy",
         "quarterly_consumption_usd": [50000, 50000, 55000, 55000, 60000, 60000, 60000, 60000, 60000, 60000, 60000, 60000]
       }
     ]
   }
   ```
   `growth_history` is optional (max 12 rows, real past quarters only).
   Max **8 engagements** and max **20 quarters** per engagement -- the
   template's own real, fixed capacity.
   ```
   terminal(command="PYTHONUTF8=1 python \"${HERMES_SKILL_DIR}\scripts\fill_macc_template.py\" --input-file <scratch path>")
   ```
   Lands at the same folder without the `(staged)`/`Info Needed` suffix
   -- the real, final sheet. The staged blank copy and the checklist
   file are harmless leftovers at that point; no need to delete them
   (archive-not-delete).

## Info Needed checklist shape

```markdown
# <Customer> MACC Forecast — Info Needed

## Already known (from the vault)
- MACC Term: (not yet known)
- Engagement "Azure Data Manager for Energy" — expected_consumption: "around $50k/month" (from its own Opportunity note)

## Still needed
- MACC Term (months)
- Forecast Start Quarter
- Last MACC Size (USD)
- Last MACC Consumption End (USD/quarter run-rate)
- Last MACC End Date
- Assumed Forward QoQ Growth Rate (%)
- For "Azure Data Manager for Energy": confirm/refine its quarterly consumption shape (flat / ramping / other) -- a single figure is enough, I can fill the rest smartly
- (repeat per engagement, including any new engagement not yet in an Opportunity note)

Fill in what you can, tell me when it's ready, and I'll generate the real sheet.
```

Adapt the real fields to what's actually missing for that customer --
never include a field that's already fully known.

## What you tell Mahmoud

**Operator's own explicit answer: "Just the Vault for What's APP you can
tell me its ready."** Never attach a file itself -- just confirm plainly
what you did (staged + checklist, or the final sheet is ready) and name
the real path.

## Pitfalls

- **Never wrap a script in `bash -lc "..."`** -- same categorical Hermes
  `terminal`-tool approval-block documented throughout this vault's
  Skills; a bare `python ...` command with the script's own full
  absolute path runs without a prompt.
- **Never invent an engagement, a quarterly figure, or a growth-history
  entry.** Every real number here should trace back to something
  Mahmoud confirmed or a real Opportunity note.
- **More than 8 real engagements, or more than 20 real quarters, for one
  customer**: the template's own fixed capacity is 8 rows / 20 quarter
  columns -- exceeding either is a real, hard error (`fill_macc_
  template.py` refuses rather than corrupting the sheet, confirmed live
  2026-08-24: an earlier version silently grew the Engagements table
  into the Quarterly Forecast section below it). Say so plainly to
  Mahmoud rather than trying to cram more in.

## Verification

- After Step 1, confirm both the staged `.xlsx` and the `Info Needed.md`
  landed at the real customer folder.
- After Step 2, confirm the returned `path` is real and that what you
  wrote matches what was actually confirmed -- a wrong quarterly figure
  produces a wrong Estimated Total MACC Size silently, since the formula
  has no way to know the input itself was wrong.
