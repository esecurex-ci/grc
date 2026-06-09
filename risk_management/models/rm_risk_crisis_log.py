from odoo import models, fields


class RiskCrisisLog(models.Model):
    _name = 'risk.crisis.log'
    _description = 'Crisis Log'

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True,
        ondelete='cascade'
    )

    log_date = fields.Datetime(
        required=True
    )

    title = fields.Char(
        required=True
    )

    description = fields.Html()

    author_id = fields.Many2one(
        'hr.employee'
    )