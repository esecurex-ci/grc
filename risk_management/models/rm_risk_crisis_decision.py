from odoo import models, fields


class RiskCrisisDecision(models.Model):
    _name = 'risk.crisis.decision'
    _description = 'Crisis Decision'

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True,
        ondelete='cascade'
    )

    decision_date = fields.Datetime(
        required=True
    )

    title = fields.Char(
        required=True
    )

    description = fields.Html()

    decision_maker_id = fields.Many2one(
        'hr.employee'
    )