"""Looks up real, current Azure prices from Microsoft's own public Retail
Prices API (https://prices.azure.com/api/retail/prices) -- no API key, no
Azure subscription needed, confirmed live 2026-08-23. Mechanical only: it
returns every real matching price row for the given filters, plus a
convenience monthly-cost projection for hourly-billed rows. It never picks
"the one right answer" for you -- when Azure genuinely has more than one
real variant (pay-as-you-go vs. Spot, Windows vs. Linux, different meter
names for the same SKU), that judgment call belongs to whoever is
interpreting the result, not to this script.

Usage (always call directly by its own full path, never wrapped in
`bash -lc` or any other shell -- same rule as every other script in this
vault):
    python lookup_azure_price.py --service-name "Virtual Machines" \
        --region uaenorth --search "D4s v5" --limit 10

    python lookup_azure_price.py --service-name Storage --region uaenorth \
        --search "Hot LRS"

All arguments are optional, but at least one of --service-name/--search
should be given -- an unfiltered query against Azure's own full price list
(hundreds of thousands of rows) is real but useless. Prints one JSON object
to stdout; prints a JSON object with an "error" key (still valid JSON, on
stdout) if the live API call itself fails, so a caller doesn't have to
parse stderr to tell success from failure.
"""
from __future__ import annotations

import argparse
import json
import sys

import httpx

_API_URL = "https://prices.azure.com/api/retail/prices"
_DEFAULT_HOURS_PER_MONTH = 730  # Azure's own standard "average hours in a month" convention.


def _build_filter(args: argparse.Namespace) -> str:
    clauses = [f"priceType eq '{args.price_type}'"]
    if args.service_name:
        clauses.append(f"serviceName eq '{args.service_name}'")
    if args.region:
        clauses.append(f"armRegionName eq '{args.region}'")
    if args.search:
        # OR across armSkuName/skuName/productName -- confirmed live,
        # 2026-08-23: armSkuName is reliably populated for compute
        # (Virtual Machines) but frequently BLANK for other real
        # services (Storage's own real rows -- Hot LRS, Cool GRS, etc.
        # -- carry their distinguishing name in skuName/productName
        # instead, armSkuName empty). A single contains(armSkuName, ...)
        # filter silently returned zero matches for every real Storage
        # SKU until this was widened.
        escaped = args.search.replace("'", "''")
        clauses.append(
            f"(contains(armSkuName, '{escaped}') or contains(skuName, '{escaped}') or contains(productName, '{escaped}'))"
        )
    return " and ".join(clauses)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service-name", default=None, help="Real Azure serviceName, e.g. 'Virtual Machines', 'Storage', 'Azure Database for PostgreSQL'.")
    parser.add_argument("--region", default=None, help="Real Azure armRegionName, e.g. 'uaenorth', 'eastus'.")
    parser.add_argument("--search", default=None, help="Substring matched against armSkuName (case-sensitive per the API's own contains()).")
    parser.add_argument("--price-type", default="Consumption", help="Consumption (default), Reservation, or DevTestConsumption.")
    parser.add_argument("--currency", default="USD")
    parser.add_argument("--limit", type=int, default=20, help="Max rows returned (the live API itself may return more; this trims client-side).")
    parser.add_argument("--hours-per-month", type=float, default=_DEFAULT_HOURS_PER_MONTH, help="Used only for the estimated_monthly_cost convenience field on hourly-billed rows.")
    args = parser.parse_args()

    if not args.service_name and not args.search:
        print(json.dumps({"error": "at least one of --service-name or --search is required"}))
        return 1

    odata_filter = _build_filter(args)
    try:
        response = httpx.get(
            _API_URL,
            params={"$filter": odata_filter, "currencyCode": args.currency},
            timeout=20.0,
        )
        response.raise_for_status()
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        print(json.dumps({"error": f"Azure Retail Prices API call failed: {exc}", "filter": odata_filter}))
        return 1

    items = []
    for row in data.get("Items", [])[: args.limit]:
        unit_price = row.get("unitPrice")
        unit = row.get("unitOfMeasure") or ""
        estimated_monthly_cost = None
        if isinstance(unit_price, (int, float)) and unit.strip().lower() in ("1 hour", "hour"):
            estimated_monthly_cost = round(unit_price * args.hours_per_month, 2)
        items.append({
            "armSkuName": row.get("armSkuName"),
            "productName": row.get("productName"),
            "meterName": row.get("meterName"),
            "skuName": row.get("skuName"),
            "unitPrice": unit_price,
            "unitOfMeasure": unit,
            "currencyCode": row.get("currencyCode"),
            "armRegionName": row.get("armRegionName"),
            "type": row.get("type"),
            "estimated_monthly_cost": estimated_monthly_cost,
        })

    print(json.dumps({
        "filter": odata_filter,
        "total_matches_before_limit": data.get("Count"),
        "returned": len(items),
        "items": items,
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
