from odoo import api, fields, models, _


class RiskSubprocess(models.Model):
    _name = 'risk.subprocess'
    _description = 'Sous-processus'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'function_id, name'
    _rec_name = 'name'

    name = fields.Char(string='Nom du sous-processus', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)
    description = fields.Html(string='Description')

    # Relations hiérarchiques
    function_id = fields.Many2one(
        'risk.function',
        string='Fonction',
        required=True,
        tracking=True,
        ondelete='cascade'
    )

    # Responsables
    owner_id = fields.Many2one('hr.employee', string='Responsable', tracking=True)

    # KRI associés
    kri_ids = fields.One2many(
        'risk.kri',
        'subprocess_id',
        string='KRI'
    )

    # Statistiques
    kri_count = fields.Integer(
        compute='_compute_kri_count',
        string="Nombre de KRI"
    )

    active = fields.Boolean(default=True)

    @api.depends('kri_ids')
    def _compute_kri_count(self):
        for record in self:
            record.kri_count = len(record.kri_ids)