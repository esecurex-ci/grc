from odoo import api, fields, models, _


class RiskGeneric(models.Model):
    _name = 'risk.generic'
    _description = 'Risque générique'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='Risque générique', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)
    description = fields.Html(string='Description')

    # Références
    reference = fields.Char(string='Référence')

    # KRI associés
    kri_ids = fields.One2many(
        'risk.kri',
        'risk_generic_id',
        string='KRI'
    )

    active = fields.Boolean(default=True)