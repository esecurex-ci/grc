from odoo import models, fields


class RiskCrisisCommunication(models.Model):
    _name = 'risk.crisis.communication'
    _description = 'Crisis Communication'

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True,
        ondelete='cascade'
    )

    communication_date = fields.Datetime(
        required=True
    )

    audience = fields.Selection(
        [
            ('employees', 'Employees'),
            ('clients', 'Clients'),
            ('regulator', 'Regulator'),
            ('media', 'Media'),
            ('board', 'Board')
        ]
    )

    subject = fields.Char()

    message = fields.Html()

    sender_id = fields.Many2one(
        'hr.employee'
    )