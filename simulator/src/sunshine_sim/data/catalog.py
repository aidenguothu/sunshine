"""Versioned JSON adapters. Import does not certify or approve product data."""

import json
from dataclasses import asdict

from sunshine_sim.engine.models import CentralizerSpec, ForceDeflectionPoint
from sunshine_sim.engine.product import ProductInput


def load_catalog(text: str) -> tuple[ProductInput, ...]:
    if len(text) > 1_000_000:
        raise ValueError("Catalog exceeds 1 MB")
    try:
        data = json.loads(text)
        if data["schema_version"] != "0.3":
            raise ValueError("Unsupported catalog schema")
        rows = data["products"]
        if not isinstance(rows, list) or not 1 <= len(rows) <= 100:
            raise ValueError("Catalog must contain 1 to 100 products")
        products = []
        for row in rows:
            row = dict(row)
            spec = dict(row.pop("spec"))
            spec["restoring_curve"] = tuple(
                ForceDeflectionPoint(**p) for p in spec["restoring_curve"]
            )
            products.append(ProductInput(spec=CentralizerSpec(**spec), **row))
        ids = [p.spec.product_id for p in products]
        if len(set(ids)) != len(ids):
            raise ValueError("Product IDs must be unique")
        return tuple(products)
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError(f"Malformed catalog: {exc}") from exc


def dump_catalog(products: tuple[ProductInput, ...]) -> str:
    return json.dumps(
        {"schema_version": "0.3", "products": [asdict(p) for p in products]},
        indent=2,
        allow_nan=False,
    )
