from odoo import models, fields

class RiskAsset(models.Model):
    _name = 'risk.asset'
    _description = 'Actif'

    name = fields.Char(string='Nom', required=True)

    code = fields.Char(string='Code')

    asset_type = fields.Selection([
        ('application', 'Application'),
        ('server', 'Serveur'),
        ('database', 'Base de données'),
        ('network', 'Réseau'),
        ('cloud', 'Cloud'),
        ('other', 'Autre'),
    ], string='Type d\'actif')

    description = fields.Text(string='Description')

    active = fields.Boolean(string='Actif', default=True)
