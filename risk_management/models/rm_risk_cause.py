from odoo import models, fields

class RiskCause(models.Model):
    _name = 'risk.cause'
    _description = 'Risk Cause'

    name = fields.Char(required=True)

    description = fields.Text()

    active = fields.Boolean(default=True)