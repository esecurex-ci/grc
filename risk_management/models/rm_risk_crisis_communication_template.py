from odoo import models, fields


class RiskCrisisCommunicationTemplate(models.Model):
    _name = 'risk.crisis.communication.template'
    _description = 'Crisis Communication Template'
    _order = 'name'

    name = fields.Char(
        required=True
    )

    code = fields.Char()

    audience = fields.Selection(
        [
            ('employee', 'Employees'),
            ('customer', 'Customers'),
            ('shareholder', 'Shareholders'),
            ('regulator', 'Regulator'),
            ('media', 'Media'),
            ('supplier', 'Suppliers')
        ],
        required=True
    )

    subject = fields.Char()

    body = fields.Html()

    active = fields.Boolean(
        default=True
    )