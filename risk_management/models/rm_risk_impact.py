from odoo import models, fields

class RiskImpact(models.Model):
    _name = 'risk.impact'
    _description = 'Risk Impact'

    name = fields.Char(required=True)

    description = fields.Text()

    active = fields.Boolean(default=True)