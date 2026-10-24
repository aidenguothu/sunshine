"""SI boundary conversions, survey validation and transparent screening utilities."""

import csv
import io
from math import acos, cos, degrees, isfinite, radians, sin

FACTORS = {
    "m": 1.0,
    "ft": 0.3048,
    "in": 0.0254,
    "mm": 0.001,
    "kg/m": 1.0,
    "ppf": 0.45359237 / 0.3048,
    "kg/m3": 1.0,
    "ppg": 119.8264273,
    "N": 1.0,
    "lbf": 4.4482216152605,
}


def number(value, name="value", minimum=None):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")
    return float(value)


def to_si(value, unit):
    if unit not in FACTORS:
        raise ValueError(f"Unknown unit: {unit}")
    return number(value) * FACTORS[unit]


def rigid_sor(hole, casing, rigid):
    for value in (hole, casing, rigid):
        number(value, minimum=0)
    if not hole > casing > 0 or not casing <= rigid <= hole:
        raise ValueError(
            "Require positive casing OD <= rigid OD <= hole ID, with hole ID > casing OD"
        )
    return (rigid - casing) / (hole - casing)


def beam_sag(q, length, ei):
    if number(q) < 0 or number(length) <= 0 or number(ei) <= 0:
        raise ValueError("Require q>=0, L>0 and EI>0")
    return 5 * q * length**4 / (384 * ei)


def midspan_sor(left, right, sag, clearance):
    if left is None or right is None:
        return None
    if (
        not 0 <= number(left) <= 1
        or not 0 <= number(right) <= 1
        or number(sag) < 0
        or number(clearance) <= 0
    ):
        raise ValueError("Invalid support, sag or clearance")
    return max(0, min(left, right) - sag / clearance)


def curve_sor(points, load):
    """Measured load->SOR only; never fabricate a curve from a single rating."""
    number(load, minimum=0)
    if len(points) < 2:
        return None
    points = sorted(points, key=lambda p: p["load_n"])
    for i, p in enumerate(points):
        if number(p["load_n"]) < 0 or not 0 <= number(p["sor"]) <= 1:
            raise ValueError("Invalid measured curve point")
        if i and (p["load_n"] <= points[i - 1]["load_n"] or p["sor"] > points[i - 1]["sor"]):
            raise ValueError("Curve loads must increase and SOR must not increase")
    if load < points[0]["load_n"] or load > points[-1]["load_n"]:
        return None
    for a, b in zip(points, points[1:]):
        if a["load_n"] <= load <= b["load_n"]:
            return a["sor"] + (b["sor"] - a["sor"]) * (load - a["load_n"]) / (
                b["load_n"] - a["load_n"]
            )
    return None


def validate_survey(rows):
    if not 2 <= len(rows) <= 20000:
        raise ValueError("Survey requires 2 to 20000 stations")
    result = []
    for row in rows:
        md = number(row["md_m"], "Survey MD", 0)
        inc = number(row["inclination_deg"], "Inclination")
        azi = number(row["azimuth_deg"], "Azimuth")
        if not 0 <= inc <= 180 or not 0 <= azi <= 360:
            raise ValueError("Inclination must be 0–180° and azimuth 0–360°")
        if result and md <= result[-1]["md_m"]:
            raise ValueError("Survey MD must strictly increase; duplicate stations are invalid")
        station = dict(md_m=md, inclination_deg=inc, azimuth_deg=azi % 360, dls_deg_30m=0.0)
        if result:
            a = result[-1]
            i1, i2 = radians(a["inclination_deg"]), radians(inc)
            dot = cos(i1) * cos(i2) + sin(i1) * sin(i2) * cos(radians(azi - a["azimuth_deg"]))
            station["dls_deg_30m"] = degrees(acos(max(-1, min(1, dot)))) * 30 / (md - a["md_m"])
        result.append(station)
    return result


def survey_csv(text, md_unit):
    to_si(1, md_unit)
    if md_unit not in ("m", "ft") or len(text) > 2_000_000:
        raise ValueError("Survey MD unit must be m or ft; maximum file size 2 MB")
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    aliases = {
        "md": "md_m",
        "md_m": "md_m",
        "md_ft": "md_m",
        "inclination": "inclination_deg",
        "inclination_deg": "inclination_deg",
        "inc": "inclination_deg",
        "azimuth": "azimuth_deg",
        "azimuth_deg": "azimuth_deg",
        "azi": "azimuth_deg",
    }
    mapping = {h: aliases.get(h.strip().lower()) for h in (reader.fieldnames or [])}
    if not {"md_m", "inclination_deg", "azimuth_deg"}.issubset(set(mapping.values())):
        raise ValueError("Required CSV columns: MD, Inclination, Azimuth")
    mapped = [v for v in mapping.values() if v]
    if len(mapped) != len(set(mapped)):
        raise ValueError("Ambiguous duplicate survey columns")
    headers = {h.lower() for h in (reader.fieldnames or [])}
    if ("md_m" in headers and md_unit != "m") or ("md_ft" in headers and md_unit != "ft"):
        raise ValueError("CSV depth header conflicts with selected MD unit")
    try:
        rows = [
            {
                v: float(row[k]) * (FACTORS[md_unit] if v == "md_m" else 1)
                for k, v in mapping.items()
                if v
            }
            for row in reader
        ]
        return validate_survey(rows)
    except (TypeError, KeyError) as exc:
        raise ValueError("Malformed survey CSV") from exc


def hole_csv(text, depth_unit, diameter_unit):
    """Explicit-unit interval import; boundary validation is performed with the job."""
    if depth_unit not in ("m", "ft") or diameter_unit not in ("mm", "in", "m"):
        raise ValueError("Select explicit m/ft depth and mm/in/m diameter units")
    if len(text) > 2_000_000:
        raise ValueError("Hole CSV exceeds 2 MB")
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    aliases = {
        "topmd": "top_md_m",
        "top_md": "top_md_m",
        "top_md_m": "top_md_m",
        "bottommd": "bottom_md_m",
        "bottom_md": "bottom_md_m",
        "bottom_md_m": "bottom_md_m",
        "holeid": "hole_id_m",
        "hole_id": "hole_id_m",
        "hole_id_m": "hole_id_m",
        "restrictionid": "restriction_id_m",
        "restriction_id": "restriction_id_m",
        "restriction_id_m": "restriction_id_m",
        "source": "source",
    }
    mapping = {h: aliases.get(h.strip().lower()) for h in (reader.fieldnames or [])}
    if not {"top_md_m", "bottom_md_m", "hole_id_m"}.issubset(set(mapping.values())):
        raise ValueError(
            "Required columns: TopMD, BottomMD, HoleID; optional RestrictionID, Source"
        )
    if (
        any(
            k.lower().endswith("_m") and v in ("top_md_m", "bottom_md_m")
            for k, v in mapping.items()
        )
        and depth_unit != "m"
    ):
        raise ValueError("Depth header _m conflicts with selected unit")
    if (
        any(
            k.lower().endswith("_m") and v in ("hole_id_m", "restriction_id_m")
            for k, v in mapping.items()
        )
        and diameter_unit != "m"
    ):
        raise ValueError("Diameter header _m conflicts with selected unit")
    mapped = [v for v in mapping.values() if v]
    if len(mapped) != len(set(mapped)):
        raise ValueError("Ambiguous duplicate hole columns")
    rows = []
    try:
        for row in reader:
            values = {"restriction_id_m": None, "source": "customer supplied CSV"}
            for k, v in mapping.items():
                if not v:
                    continue
                if v == "source":
                    values[v] = row[k]
                else:
                    values[v] = (
                        None
                        if v == "restriction_id_m" and not row[k]
                        else to_si(
                            float(row[k]),
                            depth_unit if v in ("top_md_m", "bottom_md_m") else diameter_unit,
                        )
                    )
            rows.append(values)
        if not rows:
            raise ValueError("Hole CSV is empty")
        return rows
    except (KeyError, TypeError) as exc:
        raise ValueError("Malformed hole CSV") from exc
