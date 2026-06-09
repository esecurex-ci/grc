from odoo import models, fields

class RiskRegulation(models.Model):
    _name = 'risk.regulation'
    _description = 'Regulation'

    name = fields.Char(required=True)

    code = fields.Char()

    description = fields.Text()

    active = fields.Boolean(default=True)