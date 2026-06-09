from odoo import models, fields


class RiskRootCause(models.Model):
    _name = 'risk.root.cause'
    _description = 'Root Cause'

    incident_id = fields.Many2one(
        'risk.incident',
        required=True,
        ondelete='cascade'
    )

    description = fields.Html(
        required=True
    )

    cause_type = fields.Selection(
        [
            ('human', 'Human'),
            ('process', 'Process'),
            ('technology', 'Technology'),
            ('external', 'External')
        ]
    )

    confirmed = fields.Boolean(
        default=False
    )