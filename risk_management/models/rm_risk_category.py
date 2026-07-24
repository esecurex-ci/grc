from odoo import models, fields

class RiskCategory(models.Model):
    _name = 'risk.category'
    _description = 'Categorie de Risque '
    _order = 'code'

    name = fields.Char(required=True)
    code = fields.Char(required=True)

    description = fields.Text()

    active = fields.Boolean(default=True)

    color = fields.Char(String='Couleur')

    _sql_constraints = [
        ('risk_category_code_unique',
         'unique(code)',
         'Code must be unique.')
    ]