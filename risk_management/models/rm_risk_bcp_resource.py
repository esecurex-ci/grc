from odoo import models, fields


class RiskBcpResource(models.Model):
    _name = 'risk.bcp.resource'
    _description = 'BCP Resource'

    bcp_id = fields.Many2one(
        'risk.bcp.plan',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        required=True
    )

    resource_type = fields.Selection(
        [
            ('human', 'Human'),
            ('application', 'Application'),
            ('server', 'Server'),
            ('facility', 'Facility'),
            ('provider', 'Provider')
        ]
    )

    description = fields.Html()