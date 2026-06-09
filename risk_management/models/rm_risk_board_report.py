from odoo import models, fields


class RiskBoardReport(models.Model):
    _name = 'risk.board.report'
    _description = 'Board Report'

    name = fields.Char(
        required=True
    )

    report_date = fields.Date()

    executive_summary = fields.Html()

    top_risks = fields.Html()

    compliance_status = fields.Html()

    audit_summary = fields.Html()

    incident_summary = fields.Html()

    crisis_summary = fields.Html()

    recommendation = fields.Html()