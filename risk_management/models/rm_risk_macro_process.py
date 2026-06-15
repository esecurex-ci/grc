from odoo import models, fields, api


class RiskMacroProcess(models.Model):
    _name = 'risk.macro.process'
    _description = 'Risk Macro Process'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Macro Processus',
        required=True,
        tracking=True
    )

    code = fields.Char(
        string='Code',
        help='Code unique du macro-processus',
        tracking=True
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Ordre d\'affichage'
    )

    description = fields.Html(
        string='Description'
    )

    color = fields.Integer(
        string='Color',
        help='Couleur pour l\'affichage kanban'
    )

    image_128 = fields.Image(
        string='Icone',
        max_width=128,
        max_height=128,
        help='Image représentant le macro-processus'
    )

    owner_id = fields.Many2one(
        'hr.employee',
        string='Responsable',
        tracking=True
    )

    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('active', 'Actif'),
            ('archived', 'Archivé')
        ],
        string='Statut',
        default='draft',
        tracking=True
    )

    # Relations
    process_ids = fields.One2many(
        'risk.process',
        'macro_process_id',
        string='Processus'
    )

    # Champs statistiques
    process_count = fields.Integer(
        compute='_compute_counts',
        string='Nombre de processus'
    )

    activity_count = fields.Integer(
        compute='_compute_counts',
        string='Nombre d\'activités'
    )

    risk_count = fields.Integer(
        compute='_compute_counts',
        string='Nombre de risques'
    )

    critical_risk_count = fields.Integer(
        compute='_compute_counts',
        string='Risques critiques'
    )

    @api.depends('process_ids', 'process_ids.activity_ids', 'process_ids.activity_ids.risk_ids')
    def _compute_counts(self):
        for record in self:
            record.process_count = len(record.process_ids)

            activities = record.process_ids.mapped('activity_ids')
            record.activity_count = len(activities)

            risks = activities.mapped('risk_ids')
            record.risk_count = len(risks)

            record.critical_risk_count = len(
                risks.filtered(lambda r: getattr(r, 'risk_level', '0') in ['4', '5', 'critical', 'high'])
            )

    def action_view_processes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Processus',
            'res_model': 'risk.process',
            'view_mode': 'tree,form',
            'domain': [('macro_process_id', '=', self.id)],
            'context': {'default_macro_process_id': self.id},
        }

    def action_view_activities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Activités',
            'res_model': 'risk.activity',
            'view_mode': 'tree,form',
            'domain': [('macro_process_id', '=', self.id)],
            'context': {'default_macro_process_id': self.id},
        }

    def action_view_risks(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Risques',
            'res_model': 'risk.risk',
            'view_mode': 'tree,form',
            'domain': [('macro_process_id', '=', self.id)],
            'context': {'default_macro_process_id': self.id},
        }

    def action_activate(self):
        for record in self:
            record.state = 'active'

    def action_archive(self):
        for record in self:
            record.state = 'archived'

    def action_draft(self):
        for record in self:
            record.state = 'draft'