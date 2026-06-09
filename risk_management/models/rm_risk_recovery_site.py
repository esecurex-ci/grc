from odoo import models, fields


class RiskRecoverySite(models.Model):
    _name = 'risk.recovery.site'
    _description = 'Recovery Site'

    name = fields.Char(
        required=True
    )

    location = fields.Char()

    site_type = fields.Selection(
        [
            ('cold', 'Cold Site'),
            ('warm', 'Warm Site'),
            ('hot', 'Hot Site')
        ]
    )

    capacity = fields.Text()

    active = fields.Boolean(
        default=True
    )