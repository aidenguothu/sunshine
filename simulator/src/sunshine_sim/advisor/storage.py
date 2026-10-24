"""Explicit single-workspace snapshots; never a public/multi-tenant data service."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from sunshine_sim.advisor.catalog import dump_skus, load_skus
from sunshine_sim.advisor.service import validate_job


def bundle(job, products):
    validate_job(job)
    return json.dumps(
        dict(
            schema_version="advisor-1",
            created_at_utc=datetime.now(timezone.utc).isoformat(),
            job=job,
            catalog=json.loads(dump_skus(products)),
        ),
        indent=2,
        allow_nan=False,
    )


def unbundle(text):
    if len(text) > 3_000_000:
        raise ValueError("Saved job exceeds 3 MB")
    try:
        value = json.loads(text)
        if value["schema_version"] != "advisor-1":
            raise ValueError("Unsupported advisor snapshot; old simulator jobs remain unchanged")
        validate_job(value["job"])
        products = load_skus(json.dumps(value["catalog"]))
        if value["job"].get("selected_sku") not in {p.sku for p in products}:
            raise ValueError("Saved job selected SKU is absent from its catalog")
        return value["job"], products
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"Invalid saved job: {exc}") from exc


def save_local(root: Path, slot: str, text: str):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", slot):
        raise ValueError("Save slot must use 1–60 letters, numbers, underscore or hyphen")
    unbundle(text)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / f"{slot}.json"
    temporary = root / f"{slot}.tmp"
    temporary.write_text(text)
    temporary.replace(destination)
    return destination
