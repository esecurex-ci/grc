from odoo import models, fields

class RiskCause(models.Model):
    _name = 'risk.cause'
    _description = 'Causes du Risque'

    name = fields.Char(required=True, string='Désignation')

    description = fields.Text()

    active = fields.Boolean(default=True)