from odoo import models, fields


class RiskCrisisContactDirectory(models.Model):
    _name = 'risk.crisis.contact.directory'
    _description = 'Crisis Contact Directory'
    _order = 'name'

    name = fields.Char(
        required=True
    )

    organization = fields.Char()

    role = fields.Char()

    mobile = fields.Char()

    email = fields.Char()

    priority_level = fields.Selection(
        [
            ('critical', 'Critical'),
            ('high', 'High'),
            ('normal', 'Normal')
        ],
        default='normal'
    )

    available_24x7 = fields.Boolean()