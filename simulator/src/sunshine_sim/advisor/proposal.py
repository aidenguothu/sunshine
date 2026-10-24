# ruff: noqa: E501
# HTML/CSS templates retain readable markup without changing rendered whitespace.
"""Offline print-ready sales proposals. No email/network side effects."""

from datetime import datetime, timezone
from html import escape


def e(value):
    return escape("Not supplied" if value is None or value == "" else str(value), quote=True)


def table(headers, rows):
    return (
        "<table><thead><tr>"
        + "".join(f"<th>{e(h)}</th>" for h in headers)
        + "</tr></thead><tbody>"
        + "".join("<tr>" + "".join(f"<td>{e(v)}</td>" for v in row) + "</tr>" for row in rows)
        + "</tbody></table>"
    )


def rfq_text(job, result, contact):
    product = result["product_snapshot"]
    return (
        "NON-BINDING REQUEST FOR QUOTATION — NOT AN ENGINEERING APPROVAL\n"
        f"{result['banner']}\nJob: {job['job_name']} | Well: {job.get('well_name', '')}\n"
        f"SKU: {product['sku']} | Drawing/revision: {product['revision'] or 'required'}\n"
        + "\n".join(
            f"{b['sku']}: {b['quantity']} units ({b['description']})" for b in result["bom"]
        )
        + "\n"
        + "\n".join(f"{k}: {v}" for k, v in contact.items())
        + "\nCompany quote and responsible engineer review required.\n"
        + result["disclaimer"]
    )


def proposal_html(job, result, contact, account_manager, created_at=None):
    stamp = created_at or datetime.now(timezone.utc).isoformat()
    p = result["product_snapshot"]
    validity = result["validity"]
    common = f'<div class="badge">{e(result["banner"])}</div><p class="meta">{e(job["job_name"])} · Revision {e(job["revision"])} · {e(stamp)} UTC</p>'

    def page(title, body):
        return f'<section class="page"><header><b>SUNSHINE PETROLEUM</b><span>Centralizer Placement Advisor / 扶正器选型</span></header>{common}<h1>{e(title)}</h1>{body}<footer>{e(result["model_version"])} · {e(validity)} · Non-binding sales proposal</footer></section>'

    at = [r["at_support_geometric_sor"] for r in result["placement"]]
    numeric = [v for v in at if v is not None]
    explanation = (
        f"At-centralizer geometric wall-contact SOR: {min(numeric) * 100:.2f}% to {max(numeric) * 100:.2f}%."
        if numeric
        else "At-centralizer standoff not calculable from available test data / load model."
    )
    body = '<p class="lead">Preliminary product selection and quotation support / 初步选型及报价支持</p><h2>Job & supplied inputs</h2>'
    body += table(
        ["Input", "Value"],
        [
            ("Customer / well", f"{job.get('customer', '')} / {job.get('well_name', '')}"),
            ("Analysis MD (m)", f"{job['top_md_m']:g} – {job['bottom_md_m']:g}"),
            (
                "Casing OD / ID (mm)",
                f"{job['casing_od_m'] * 1000:g} / {job['casing_id_m'] * 1000:g}"
                if job.get("casing_id_m")
                else f"{job['casing_od_m'] * 1000:g} / not supplied",
            ),
            ("Linear mass (kg/m)", job.get("mass_kg_m")),
            ("Fluid density (kg/m³)", job["fluid_density_kg_m3"]),
            (
                "Data origin / customer target",
                f"{job['data_origin']} / {100 * job['target_ratio']:g}% (not a universal standard)",
            ),
            (
                "Survey / DLS",
                f"{len(job['survey'])} stations; max {result['maximum_dls_deg_30m']:.2f} °/30m",
            ),
            (
                "Hole/restriction source",
                "; ".join(
                    f"{h['top_md_m']:g}–{h['bottom_md_m']:g} m: {h['hole_id_m'] * 1000:g} mm; {h['source']}"
                    for h in job["holes"]
                ),
            ),
        ],
    )
    body += f"<h2>Selected product · {e(p['sku'])}</h2>" + table(
        ["Attribute", "Supplied information"],
        [
            ("Manufacturer / family", f"{p['manufacturer']} / {p['family']}"),
            (
                "Datasheet / revision",
                f"{p['datasheet_reference'] or 'required'} / {p['revision'] or 'required'}",
            ),
            ("Compatibility", result["compatibility"]["status"]),
            ("Availability", p["availability"]),
            (
                "Test curve reference",
                p["curve_reference"] or "No complete applicable curve supplied",
            ),
            ("Installation rule", p["collar_rule_reference"] or "Review required"),
        ],
    )
    if len(result.get("product_snapshots", [])) > 1:
        body += "<h2>Additional selected products</h2>" + table(
            ["SKU", "Family", "Evidence / revision"],
            [
                [
                    r["sku"],
                    r["family"],
                    f"{r['datasheet_reference'] or 'required'} / {r['revision'] or 'required'}",
                ]
                for r in result["product_snapshots"]
                if r["sku"] != p["sku"]
            ],
        )
    body += f'<div class="callout"><b>{e(result["methodology"])}</b><p>{e(explanation)}</p><p>Between-centralizer standoff: NOT CALCULATED. No target-standoff optimization or run-to-bottom claim.</p></div>'
    # Draw only a supported rigid geometric figure; no bow numeric visual.
    if numeric:
        ratio = min(numeric)
        body += f'<p>Illustrative rigid support geometric SOR</p><div class="bar"><span style="width:{100 * ratio:.3f}%"></span></div><small>Wall-contact geometry only; not predicted downhole performance.</small>'
    pages = [page("Preliminary centralizer proposal", body)]
    rows = result["placement"]
    for offset in range(0, len(rows), 64):
        chunk = rows[offset : offset + 64]

        def install(part):
            return table(
                ["Joint", "MD (m)", "SKU", "Collars"],
                [[r["joint_no"], f"{r['md_m']:.3f}", r["sku"], r["stop_collar_qty"]] for r in part],
            )

        body = f"<p>{len(rows)} centralizers total. Actual joint tally; mount at {job['joint_offset_m']:g} m from joint start. Beginning/end windows and no-go zones applied.</p><p>Verify stop-collar configuration, product length and connection clearances before installation. Unknown lengths are not dimensionally verified.</p>"
        body += '<div class="schedule">' + install(chunk[:32]) + install(chunk[32:]) + "</div>"
        pages.append(
            page("Installation schedule / 安装位置" + (" — continued" if offset else ""), body)
        )
    body = table(
        ["Part / SKU", "Description", "Qty", "Company-supplied price"],
        [
            [
                b["sku"],
                b["description"],
                b["quantity"],
                "Not supplied"
                if b["unit_price"] is None
                else f"{b['unit_price']:g} {b['currency']} each; subtotal {b['total']:g}; {b['price_reference']}",
            ]
            for b in result["bom"]
        ],
    )
    body += (
        "<p>No complete project price is calculated when any BOM line is unpriced. No freight, tax or delivery commitment is implied.</p><h2>Methodology & review items</h2><ul>"
        + "".join(
            f"<li>{e(r)}</li>" for r in result["compatibility"]["blocking"] + result["reasons"]
        )
        + "</ul>"
    )
    body += f"<p>{e(result['disclaimer'])}</p><h2>Account manager / 客户经理</h2><p>{e(account_manager)}</p><h2>Request Quote / 询价</h2><p>Non-binding; verify quantities, drawings, installation rules and delivery terms with Sunshine.</p><pre>{e(rfq_text(job, result, contact))}</pre>"
    pages.append(page("Bill of materials & quotation request", body))
    return (
        """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Sunshine preliminary proposal</title><style>
body{font:12px Arial,sans-serif;color:#263c4b;background:#eaf0f2;margin:0}*{box-sizing:border-box}.toolbar{padding:18px;text-align:center;background:#173e50;color:white}.toolbar button{padding:10px 20px;cursor:pointer}.page{background:white;max-width:210mm;min-height:280mm;margin:15px auto;padding:14mm;position:relative}header{display:flex;justify-content:space-between;border-bottom:3px solid #07858a;padding-bottom:12px;font-size:10px}h1{font-size:23px}h2{font-size:15px;margin:15px 0 7px}.badge{font-weight:bold;color:#9f3c21;background:#fff2d9;padding:8px;margin-top:12px}.meta,small{font-size:10px;color:#60707a}.lead{color:#087a80}table{width:100%;border-collapse:collapse;font-size:10px}td,th{padding:5px;border-bottom:1px solid #dce4e8;text-align:left;overflow-wrap:anywhere}th{background:#ecf5f5}.schedule{display:grid;grid-template-columns:1fr 1fr;gap:10px}.schedule table{align-self:start;font-size:9px}.schedule td{padding:4px}footer{margin-top:18px;border-top:1px solid #ddd;padding-top:6px;font-size:9px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:9px Arial;background:#f4f7f8;padding:9px}.callout{background:#eef6f6;padding:10px;margin:10px 0}.bar{height:13px;background:#eee}.bar span{display:block;background:#07858a;height:100%}li{margin:4px 0}@page{size:A4;margin:8mm}@media print{body{background:white}.toolbar{display:none}.page{margin:0;min-height:0;max-width:none;padding:5mm;break-after:page}.page:last-child{break-after:auto}table,tr{break-inside:avoid}*{-webkit-print-color-adjust:exact;print-color-adjust:exact}}@media(max-width:600px){.page{padding:16px}.schedule{grid-template-columns:1fr}header{display:block}}
</style></head><body><div class="toolbar"><b>PRELIMINARY / 初步方案</b> · <button onclick="window.print()">Print / Save as PDF · 打印</button><p>Use your browser print dialog; no data is sent.</p></div>"""
        + "".join(pages)
        + "</body></html>"
    )
