---
name: azure-cost-calculator
description: Estimates real Azure infrastructure costs for a described workload, priced against Azure's own live Retail Prices API (not a guess from memory). Use this whenever asked to price, estimate, size, or budget Azure resources -- VMs, storage, databases, or a combination -- for a proposal, an opportunity, or general curiosity.
version: 0.1.0
author: second-brain
license: MIT
platforms: [windows]
metadata:
  hermes:
    tags: [azure, pricing, cost-estimate, whatsapp, conversational]
---

# Azure Cost Calculator

**Live and conversational, not cron-triggered** -- this Skill runs mid-chat
the moment someone asks you to price or size Azure infrastructure. Your own
SOUL.md already covers HOW to hold that conversation (ask the right
questions before calculating); this file covers the real mechanics of
getting a real number once you know what to price.

## The real tool: `lookup_azure_price.py`

Queries Azure's own public Retail Prices API (`prices.azure.com`) live --
no API key, no Azure subscription, confirmed real and working. Call it as
a PLAIN direct terminal command using its own full absolute path, never
wrapped in `bash -lc` or any other shell -- that gets blocked pending an
approval nobody is there to give.

```
python <this Skill's own scripts folder>\lookup_azure_price.py --service-name "Virtual Machines" --region uaenorth --search "D4s v5"
```

Real, useful `--service-name` values (Azure's own real `serviceName`
field -- match it exactly, these are not guessable from a resource's
marketing name):
- `Virtual Machines` -- compute
- `Storage` -- Blob/Disk/File storage
- `Azure Database for PostgreSQL` / `Azure Database for MySQL` / `SQL Database` -- managed databases
- `Azure App Service` -- PaaS web hosting
- `Load Balancer`, `Virtual Network`, `Bandwidth` -- networking
- `Azure Kubernetes Service` -- AKS (the control plane itself is usually
  free; you're really pricing the underlying VMs it runs on, so search
  Virtual Machines for those instead)

If you don't know the exact `serviceName`, omit it and rely on `--search`
alone (matched against the real internal SKU name, e.g. `"D4s v5"`,
`"P30"`, `"S2"`) -- still returns real rows, just a broader search.

**Region matters.** Always pass `--region` with a real Azure ARM region
code (e.g. `uaenorth`, `uaecentral`, `eastus`, `westeurope`) once you know
it -- the same SKU can price differently by tens of percent across
regions. If you're not sure of the exact code for a place someone named in
plain language, use your own knowledge to map it to the real ARM name
(e.g. "Dubai"/"UAE" -> `uaenorth`) rather than asking a separate question
just for that.

## Reading the result

The script's own JSON output lists every real matching row -- often more
than one per SKU (pay-as-you-go, Spot, Low Priority, Windows vs. Linux,
Reservation terms). Pick the row that actually matches what was asked
(default: standard pay-as-you-go, Linux where relevant, `Consumption`
price type) and say which one you picked if there was a real choice.
`estimated_monthly_cost` is only populated for hourly-billed rows
(`unitOfMeasure` = "1 Hour") -- for storage (billed per GB) or anything
else, do that multiplication yourself against the real quantity you were
given (e.g. `unitPrice * GB_requested`), and say what you multiplied by
so it's checkable.

An empty `items` list is a real "no match" -- the search/region/service
combination didn't hit anything in Azure's own live price list. Don't
invent a number to fill the gap; say the lookup came back empty and ask
for (or guess and confirm) a more specific service name/SKU/region.
An `error` key means the live API call itself failed (network issue,
malformed filter) -- say so honestly, don't fall back to a remembered
price.

## Multi-resource estimates

For "a VM plus a database plus storage"-style asks, call the script once
per real resource, then add the real `estimated_monthly_cost`/your own
computed monthly figures into one total. Present the real line-item
breakdown (what you looked up, what you picked, what it costs) alongside
the total -- never just a bare final number with no visible working.

## What this Skill doesn't do

It doesn't write anything to the vault, doesn't create or update an
Opportunity, and doesn't remember a prior estimate across separate
conversations -- it's a live calculator, not a filing system. If asked to
also save this estimate somewhere real, say you can't do that yourself.
