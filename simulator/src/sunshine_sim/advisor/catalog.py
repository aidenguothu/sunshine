"""Sales SKU master; independent of the experimental installed-spring catalog."""

import csv
import io
import json
from dataclasses import asdict, dataclass

from sunshine_sim.advisor.engineering import number

DEMO = "SYNTHETIC EXAMPLE — REPLACE BEFORE CUSTOMER USE"


@dataclass(frozen=True)
class SalesSKU:
    sku: str
    manufacturer: str
    family: str
    casing_od_m: float
    hole_min_m: float
    hole_max_m: float
    rigid_od_m: float | None = None
    free_od_m: float | None = None
    compressed_od_m: float | None = None
    minimum_bore_m: float | None = None
    length_m: float | None = None
    collars_per_unit: int = 0
    collar_sku: str = ""
    collar_rule_reference: str = ""
    starting_force_n: float | None = None
    running_force_n: float | None = None
    restoring_force_at_67_n: float | None = None
    curve: tuple = ()
    curve_hole_m: float | None = None
    curve_reference: str = ""
    datasheet_reference: str = ""
    revision: str = ""
    availability: str = "Not supplied"
    installation_notes: str = ""
    unit_price: float | None = None
    currency: str = ""
    price_reference: str = ""
    demo: bool = True
    approved_for_customers: bool = False

    def __post_init__(self):
        if not self.sku.strip() or not self.manufacturer.strip():
            raise ValueError("SKU and manufacturer are required")
        if type(self.demo) is not bool or type(self.approved_for_customers) is not bool:
            raise ValueError("Demo and approval flags must be boolean")
        if self.sku.upper().startswith("DEMO") or "FICTIONAL" in self.manufacturer.upper():
            if not self.demo:
                raise ValueError("Synthetic SKU cannot be relabelled as a real Sunshine product")
        if self.demo and self.approved_for_customers:
            raise ValueError("Synthetic data cannot be approved for customer use")
        if self.approved_for_customers and not (self.datasheet_reference and self.revision):
            raise ValueError("Company approval metadata needs datasheet reference and revision")
        if self.family not in ("rigid", "bow", "semi_rigid", "molded"):
            raise ValueError("Unknown centralizer family")
        for name in ("casing_od_m", "hole_min_m", "hole_max_m"):
            if number(getattr(self, name), name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.hole_min_m > self.hole_max_m or self.hole_min_m <= self.casing_od_m:
            raise ValueError("Invalid supported hole range")
        for name in (
            "rigid_od_m",
            "free_od_m",
            "compressed_od_m",
            "minimum_bore_m",
            "length_m",
            "curve_hole_m",
            "starting_force_n",
            "running_force_n",
            "restoring_force_at_67_n",
            "unit_price",
        ):
            v = getattr(self, name)
            if v is not None:
                number(v, name, 0)
                if name.endswith("_m") and v == 0:
                    raise ValueError(f"{name} must be positive when supplied")
        if self.family == "rigid" and (
            self.rigid_od_m is None or self.rigid_od_m < self.casing_od_m
        ):
            raise ValueError("Rigid OD must be supplied and at least casing OD")
        if self.compressed_od_m is not None and self.compressed_od_m < self.casing_od_m:
            raise ValueError("Compressed OD cannot be below casing OD")
        if self.compressed_od_m and self.free_od_m and self.compressed_od_m > self.free_od_m:
            raise ValueError("Compressed OD cannot exceed free OD")
        if type(self.collars_per_unit) is not int or not 0 <= self.collars_per_unit <= 20:
            raise ValueError(
                "Stop-collar quantity must be an integer 0–20 from the installation rule"
            )
        if self.unit_price is not None and not (self.currency and self.price_reference):
            raise ValueError("A supplied price needs currency and company quote reference")
        if self.curve:
            from sunshine_sim.advisor.engineering import curve_sor

            curve_sor(self.curve, 0)


def load_skus(text):
    if len(text) > 2_000_000:
        raise ValueError("Catalog exceeds 2 MB")
    try:
        data = json.loads(text)
        if data["schema_version"] != "sales-1":
            raise ValueError("Expected sales-1 catalog schema")
        if not 1 <= len(data["products"]) <= 500:
            raise ValueError("Catalog requires 1–500 SKUs")
        items = []
        for r in data["products"]:
            r = dict(r)
            r["curve"] = tuple(r.get("curve", ()))
            items.append(SalesSKU(**r))
        if len({p.sku for p in items}) != len(items):
            raise ValueError("Duplicate SKU")
        return tuple(items)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"Invalid sales catalog: {exc}") from exc


def dump_skus(products):
    return json.dumps(
        dict(schema_version="sales-1", products=[asdict(p) for p in products]),
        indent=2,
        allow_nan=False,
    )


def import_sku_csv(text):
    """Starter-pack dimension CSV. No approval, price or certificate is inferred."""
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    required = {
        "SKU",
        "Manufacturer",
        "Family",
        "Casing_OD_mm",
        "Nominal_Hole_ID_mm",
        "Stop_Collars_Per_Unit",
        "Status",
    }
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError("Missing product CSV columns; use the provided product CSV template")
    products = []
    try:
        for row in reader:

            def mm(name):
                return float(row[name]) * 0.001 if row.get(name) else None

            synthetic = "SYNTHETIC" in row["Status"].upper() or row["SKU"].startswith("DEMO")
            products.append(
                SalesSKU(
                    sku=row["SKU"],
                    manufacturer=row["Manufacturer"],
                    family=row["Family"],
                    casing_od_m=mm("Casing_OD_mm"),
                    hole_min_m=mm("Nominal_Hole_ID_mm"),
                    hole_max_m=mm("Nominal_Hole_ID_mm"),
                    rigid_od_m=mm("Rigid_OD_mm"),
                    free_od_m=mm("Bow_Free_OD_mm"),
                    compressed_od_m=mm("Bow_Compressed_OD_mm"),
                    restoring_force_at_67_n=float(row["Restoring_Force_at_67_pct_N"])
                    if row.get("Restoring_Force_at_67_pct_N")
                    else None,
                    collars_per_unit=int(row["Stop_Collars_Per_Unit"]),
                    demo=synthetic,
                )
            )
        return load_skus(dump_skus(products))
    except (KeyError, TypeError) as exc:
        raise ValueError("Malformed product CSV") from exc
