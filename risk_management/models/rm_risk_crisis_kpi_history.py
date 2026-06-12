from odoo import models, fields


class RiskCrisisKpiHistory(models.Model):
    _name = 'risk.crisis.kpi.history'
    _description = 'Crisis KPI History'
    _order = 'snapshot_date desc'

    snapshot_date = fields.Date(
        required=True,
        default=fields.Date.today
    )

    open_crisis_count = fields.Integer()

    critical_crisis_count = fields.Integer()

    mttr_hours = fields.Float()

    open_action_count = fields.Integer()

    overdue_decision_count = fields.Integer()

    regulator_communication_count = fields.Integer()

    crisis_management_score = fields.Float()