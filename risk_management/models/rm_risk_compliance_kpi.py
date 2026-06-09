from odoo import models, fields


class RiskComplianceKpi(models.Model):
    _name = 'risk.compliance.kpi'
    _description = 'Compliance KPI'

    name = fields.Char(
        required=True
    )

    period = fields.Char()

    compliant_count = fields.Integer()

    partial_count = fields.Integer()

    non_compliant_count = fields.Integer()

    overdue_action_count = fields.Integer()

    compliance_rate = fields.Float()