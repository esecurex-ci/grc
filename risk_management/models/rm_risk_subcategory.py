from odoo import models, fields

class RiskSubCategory(models.Model):
    _name = 'risk.subcategory'
    _description = 'Risk SubCategory'

    name = fields.Char(required=True)

    category_id = fields.Many2one(
        'risk.category',
        required=True,
        ondelete='restrict'
    )

    description = fields.Text()

    active = fields.Boolean(default=True)