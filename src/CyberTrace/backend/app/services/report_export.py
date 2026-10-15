"""Report export generation: JSON (full case export), CSV (zipped timeline
+ parse_errors), and PDF (human-readable summary), per PROJECT_PLAN.md
section 10. All three pull the same real DB rows already used by the
Timeline/Evidence/Parse-Errors pages -- no separate invented statistics.
"""
import csv
import io
import json
import zipfile
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table as PdfTable, TableStyle

from app.models.case import Case
from app.models.evidence import EvidenceFile
from app.models.log_record import LogRecord
from app.models.parse_error import ParseError, ParsingGap


def build_json_export(
    case: Case,
    evidence_files: list[EvidenceFile],
    log_records: list[LogRecord],
    parse_errors: list[ParseError],
    parsing_gaps: list[ParsingGap],
) -> dict:
    """Full machine-readable case export -- the "ground truth" format."""
    return {
        "case": {
            "id": case.id,
            "name": case.name,
            "description": case.description,
            "is_synthetic": case.is_synthetic,
            "scenario_key": case.scenario_key,
            "created_at": case.created_at.isoformat(),
        },
        "evidence_files": [
            {
                "id": e.id,
                "original_filename": e.original_filename,
                "detected_format": e.detected_format,
                "sha256_hash": e.sha256_hash,
                "byte_size": e.byte_size,
                "uploaded_at": e.uploaded_at.isoformat(),
                "source_timezone_assumption": e.source_timezone_assumption,
            }
            for e in evidence_files
        ],
        "log_records": [
            {
                "id": r.id,
                "evidence_file_id": r.evidence_file_id,
                "line_number": r.line_number,
                "raw_line": r.raw_line,
                "event_time_utc": r.event_time_utc.isoformat(),
                "original_timezone": r.original_timezone,
                "source_ip": r.source_ip,
                "user_or_actor": r.user_or_actor,
                "event_type": r.event_type,
                "message": r.message,
                "severity": r.severity,
            }
            for r in log_records
        ],
        "parse_errors": [
            {
                "id": e.id,
                "evidence_file_id": e.evidence_file_id,
                "line_number": e.line_number,
                "raw_line": e.raw_line,
                "reason": e.reason,
                "parser_name": e.parser_name,
            }
            for e in parse_errors
        ],
        "parsing_gaps": [
            {
                "id": g.id,
                "evidence_file_id": g.evidence_file_id,
                "gap_start_line": g.gap_start_line,
                "gap_end_line": g.gap_end_line,
                "description": g.description,
            }
            for g in parsing_gaps
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_csv_export_zip(
    log_records: list[LogRecord],
    parse_errors: list[ParseError],
) -> bytes:
    """Zips two separate CSVs (timeline records, parse errors) so each file
    keeps a consistent column set rather than one mixed CSV."""
    records_buf = io.StringIO()
    records_writer = csv.writer(records_buf)
    records_writer.writerow(
        [
            "line_number",
            "event_time_utc",
            "original_timezone",
            "source_ip",
            "user_or_actor",
            "event_type",
            "severity",
            "message",
            "raw_line",
            "evidence_file_id",
        ]
    )
    for r in log_records:
        records_writer.writerow(
            [
                r.line_number,
                r.event_time_utc.isoformat(),
                r.original_timezone,
                r.source_ip or "",
                r.user_or_actor or "",
                r.event_type,
                r.severity,
                r.message,
                r.raw_line,
                r.evidence_file_id,
            ]
        )

    errors_buf = io.StringIO()
    errors_writer = csv.writer(errors_buf)
    errors_writer.writerow(["line_number", "reason", "parser_name", "raw_line", "evidence_file_id"])
    for e in parse_errors:
        errors_writer.writerow([e.line_number, e.reason, e.parser_name, e.raw_line, e.evidence_file_id])

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("timeline_records.csv", records_buf.getvalue())
        zf.writestr("parse_errors.csv", errors_buf.getvalue())
    return zip_buf.getvalue()


def build_pdf_report(
    case: Case,
    evidence_files: list[EvidenceFile],
    log_records: list[LogRecord],
    parse_errors: list[ParseError],
    parsing_gaps: list[ParsingGap],
) -> bytes:
    """Human-readable incident report: cover page (case name, generated
    date, evidence hash list), summary counts, the timeline, and an
    explicit "Unparsed / anomalous records" section -- per
    PROJECT_PLAN.md section 10, gaps/errors must be visible in the
    delivered report, not just the UI."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"CyberTrace Incident Report: {case.name}", styles["Title"]))
    story.append(Spacer(1, 0.15 * inch))
    generated_at = datetime.now(timezone.utc).isoformat()
    story.append(Paragraph(f"Generated: {generated_at}", styles["Normal"]))
    if case.is_synthetic:
        story.append(Paragraph("SYNTHETIC SCENARIO -- not real incident data", styles["Heading3"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Evidence files (SHA-256)", styles["Heading2"]))
    for e in evidence_files:
        story.append(Paragraph(f"{e.original_filename} — {e.sha256_hash}", styles["Code"]))
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(
        Paragraph(
            f"{len(log_records)} records, {len(parse_errors)} parse errors, "
            f"{len(parsing_gaps)} detected gaps.",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Timeline", styles["Heading2"]))
    timeline_rows = [["Timestamp (UTC)", "Source", "Event type", "Severity", "Message"]]
    for r in log_records[:500]:  # cap rows per PDF to keep the file reasonable
        timeline_rows.append(
            [
                r.event_time_utc.isoformat(),
                r.source_ip or r.user_or_actor or "",
                r.event_type,
                r.severity,
                r.message[:80],
            ]
        )
    timeline_table = PdfTable(timeline_rows, repeatRows=1)
    timeline_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 7),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    story.append(timeline_table)
    story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Unparsed / anomalous records", styles["Heading2"]))
    if not parse_errors and not parsing_gaps:
        story.append(Paragraph("None detected.", styles["Normal"]))
    else:
        for e in parse_errors:
            story.append(
                Paragraph(f"Line {e.line_number}: {e.reason} — {e.raw_line[:100]}", styles["Normal"])
            )
        for g in parsing_gaps:
            story.append(
                Paragraph(
                    f"Gap lines {g.gap_start_line}-{g.gap_end_line}: {g.description}", styles["Normal"]
                )
            )

    doc.build(story)
    return buf.getvalue()
