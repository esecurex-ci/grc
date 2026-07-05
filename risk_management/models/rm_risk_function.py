from odoo import api, fields, models, _


class RiskFunction(models.Model):
    _name = 'risk.function'
    _description = 'Fonction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(string='Nom de la fonction', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)
    description = fields.Html(string='Description')

    # Relations
    subprocess_ids = fields.One2many(
        'risk.subprocess',
        'function_id',
        string='Sous-processus'
    )

    # Responsables
    owner_id = fields.Many2one('hr.employee', string='Responsable', tracking=True)

    # Statistiques
    kri_count = fields.Integer(
        compute='_compute_kri_count',
        string="Nombre de KRI"
    )

    active = fields.Boolean(default=True)

    @api.depends('subprocess_ids.kri_ids')
    def _compute_kri_count(self):
        for record in self:
            count = 0
            for sub in record.subprocess_ids:
                count += sub.kri_count
            record.kri_count = count