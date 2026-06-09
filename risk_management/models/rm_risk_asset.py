from odoo import models, fields

class RiskAsset(models.Model):
    _name = 'risk.asset'
    _description = 'Asset'

    name = fields.Char(required=True)

    code = fields.Char()

    asset_type = fields.Selection([
        ('application', 'Application'),
        ('server', 'Server'),
        ('database', 'Database'),
        ('network', 'Network'),
        ('cloud', 'Cloud'),
        ('other', 'Other'),
    ])

    description = fields.Text()

    active = fields.Boolean(default=True)