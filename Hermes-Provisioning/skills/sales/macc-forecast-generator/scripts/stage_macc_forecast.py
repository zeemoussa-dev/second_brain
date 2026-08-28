"""CLI entry point: stage a blank copy of the real MACC Forecast template
for one real customer (2026-08-24, operator: "The Agent should Create a
copy of the template and an md file next to it under the customer and
ask me hey I looked inside our vault I found some info but it's not
enough..."). This is the FIRST half of the real two-step flow -- it does
NOT fill anything in; `fill_macc_template.py` (same Skill) does that
once the real info is actually gathered. Splitting it this way avoids
the real UX failure found live the same day: asking Mahmoud a long list
of questions in one chat message. Instead, the agent stages a real
working copy plus a companion "info needed" checklist and comes back
later once it's filled in.

Usage:
    python stage_macc_forecast.py --vault-path P --customer C

Prints {"created": true, "path": str} or {"error": str}.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

_SLUG_INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')
_TEMPLATE_RELATIVE_PATH = ("Work", "Templates", "MACC Forecast Template.xlsx")


def _slugify(text: str, max_len: int = 80) -> str:
    slug = _SLUG_INVALID_CHARS.sub("-", text).strip()
    return slug[:max_len] if slug else "Untitled"


def stage_macc_forecast(vault_path: Path, customer: str) -> dict:
    if not customer.strip():
        return {"error": "customer is required"}

    template_path = vault_path.joinpath(*_TEMPLATE_RELATIVE_PATH)
    if not template_path.is_file():
        return {"error": f"template not found at {template_path}"}

    customer_dir = vault_path / "Work" / "Customers" / _slugify(customer) / "Files" / "MACC Estimator"
    customer_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    output_path = customer_dir / f"{_slugify(customer)} MACC Forecast {today} (staged).xlsx"

    shutil.copyfile(template_path, output_path)

    return {"created": True, "path": str(output_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault-path", required=True)
    parser.add_argument("--customer", required=True)
    args = parser.parse_args()

    result = stage_macc_forecast(Path(args.vault_path), args.customer)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    raise SystemExit(main())
