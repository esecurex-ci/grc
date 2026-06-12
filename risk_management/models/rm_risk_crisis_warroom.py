from odoo import models, fields


class RiskCrisisWarroom(models.Model):
    _name = 'risk.crisis.warroom'
    _description = 'Crisis War Room'

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True
    )

    activation_date = fields.Datetime()

    location = fields.Char()

    meeting_url = fields.Char()

    status = fields.Selection(
        [
            ('inactive', 'Inactive'),
            ('active', 'Active'),
            ('closed', 'Closed')
        ],
        default='inactive'
    )

    notes = fields.Html()