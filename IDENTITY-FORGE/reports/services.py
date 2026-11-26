from datetime import datetime
from io import BytesIO

from django.core.files.base import ContentFile
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from analysis.models import AnomalyResult, RiskFinding, ZeroTrustAssessment
from audit.services import log_action
from dashboard.metrics import dashboard_metrics
from reports.models import Report


def build_report_pdf(organization, report_type, metrics, findings, anomalies, assessment):
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer, pagesize=A4, title="IdentityForge Assessment", author="IdentityForge"
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "IdentityForgeTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#D4AF37"),
        alignment=TA_LEFT,
        spaceAfter=14,
    )
    heading_style = ParagraphStyle(
        "IdentityForgeHeading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1F2A44"),
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = styles["BodyText"]
    story = [
        Paragraph("IdentityForge Security Assessment", title_style),
        Paragraph(f"Organization: {organization.name}", body_style),
        Paragraph(f"Report type: {report_type.title()}", body_style),
        Paragraph(f"Generated: {timezone.now().isoformat()}", body_style),
        Paragraph(
            "Decision-support report. Synthetic or imported data only; human review is required.",
            body_style,
        ),
        Spacer(1, 12),
    ]

    metric_rows = [
        ["Identity metric", "Value"],
        ["Total identities", metrics["total_identities"]],
        ["Privileged accounts", metrics["privileged_accounts"]],
        ["Excessive permission findings", metrics["excessive_permissions"]],
        ["Suspicious access events", metrics["suspicious_events"]],
        ["Inactive accounts", metrics["inactive_accounts"]],
        ["High-risk access relationships", metrics["high_risk_relationships"]],
        ["Open findings", metrics["open_findings"]],
        [
            "Zero Trust score",
            metrics["zero_trust_score"]
            if metrics["zero_trust_score"] is not None
            else "Not assessed",
        ],
    ]
    metric_table = Table(metric_rows, colWidths=[330, 140])
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2A44")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAB4C4")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F4F8")]),
            ]
        )
    )
    story.extend([Paragraph("Executive Metrics", heading_style), metric_table])

    finding_rows = [["Severity", "Title", "NIST CSF", "Score"]]
    for finding in findings:
        finding_rows.append(
            [
                finding.get_severity_display(),
                finding.title[:55],
                ", ".join(finding.nist_controls),
                finding.score,
            ]
        )
    finding_table = Table(finding_rows, colWidths=[70, 260, 125, 50])
    finding_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F2A44")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#AAB4C4")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    story.extend([Paragraph("Prioritized Findings", heading_style), finding_table])

    story.append(Paragraph("Anomaly Evidence", heading_style))
    if anomalies:
        for anomaly in anomalies[:8]:
            story.append(
                Paragraph(
                    f"{anomaly.user.username} on {anomaly.event_date}: score {anomaly.anomaly_score}; {'; '.join(anomaly.reasons)}",
                    body_style,
                )
            )
    else:
        story.append(Paragraph("No anomaly results recorded for the selected scope.", body_style))

    story.append(Paragraph("Zero Trust Recommendations", heading_style))
    if assessment:
        for recommendation in assessment.recommendations:
            story.append(Paragraph(f"• {recommendation}", body_style))
    else:
        story.append(
            Paragraph("Run a Zero Trust assessment to generate recommendations.", body_style)
        )

    document.build(story)
    buffer.seek(0)
    return buffer.read()


def generate_report(organization, report_type, actor=None, ip_address=None):
    metrics = dashboard_metrics(organization)
    findings = RiskFinding.objects.filter(organization=organization).order_by("-score")[:20]
    anomalies = AnomalyResult.objects.filter(organization=organization, is_anomaly=True)[:10]
    assessment = ZeroTrustAssessment.objects.filter(organization=organization).first()
    payload = build_report_pdf(organization, report_type, metrics, findings, anomalies, assessment)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"identityforge-{report_type.lower()}-{timestamp}.pdf"
    report = Report.objects.create(
        organization=organization,
        title=f"{report_type.title()} Identity Risk Report - {organization.name}",
        report_type=report_type,
        generated_by=actor,
        summary={
            "metrics": metrics,
            "finding_count": findings.count(),
            "anomaly_count": anomalies.count(),
            "zero_trust_score": assessment.score if assessment else None,
        },
    )
    report.file.save(filename, ContentFile(payload), save=True)
    log_action(
        organization,
        actor,
        f"Generated {report_type} report",
        "Report",
        report.id,
        {"title": report.title},
        ip_address,
    )
    return report
