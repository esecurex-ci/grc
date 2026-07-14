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
        string='Séquence',
        default=10,
        help='Ordre d\'affichage'
    )

    description = fields.Html(
        string='Description'
    )

    color = fields.Integer(
        string='Couleur',
        help='Couleur pour l\'affichage kanban'
    )

    image_128 = fields.Image(
        string='Icône',
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

    # ✅ CHAMPS STATISTIQUES CORRIGÉS - Tous avec les mêmes propriétés
    process_count = fields.Integer(
        compute='_compute_counts',
        compute_sudo=True,  # ← AJOUTÉ
        store=True,  # ← store=True pour tous
        string='Nombre de processus'
    )

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Décochez pour désactiver ce macro-processus"
    )

    activity_count = fields.Integer(
        compute='_compute_counts',
        compute_sudo=True,  # ← AJOUTÉ
        store=True,  # ← store=True (cohérent avec les autres)
        string='Nombre d\'activités'
    )

    risk_count = fields.Integer(
        compute='_compute_counts',
        compute_sudo=True,  # ← AJOUTÉ
        store=True,  # ← store=True pour tous
        string='Nombre de risques'
    )

    critical_risk_count = fields.Integer(
        compute='_compute_counts',
        compute_sudo=True,  # ← AJOUTÉ
        store=True,  # ← store=True (cohérent)
        string='Risques critiques'
    )

    category = fields.Selection([
        ('pilotage', '🏛️ Processus de Pilotage'),
        ('operational', '⚙️ Processus Opérationnels'),
        ('support', '🛠️ Processus Supports'),
    ], string='Catégorie', required=True, default='operational', tracking=True, index=True)

    control_count = fields.Integer(
        compute='_compute_control_stats',
        store=True,
        string="Nombre de contrôles"
    )

    @api.depends('process_ids', 'process_ids.risk_ids')
    def _compute_counts(self):
        for record in self:
            # Nombre de processus
            record.process_count = len(record.process_ids)

            # Compter les risques et activités
            risk_count = 0
            critical_count = 0
            activity_count = 0

            for process in record.process_ids:
                # Compter les risques
                process_risks = process.risk_ids
                risk_count += len(process_risks)

                # Compter les risques critiques (niveau 5)
                for risk in process_risks:
                    if risk.risk_level == '5' or risk.inherent_level == 'critical':
                        critical_count += 1

                # Compter les activités (si le champ existe)
                if hasattr(process, 'activity_ids'):
                    activity_count += len(process.activity_ids)

            record.risk_count = risk_count
            record.critical_risk_count = critical_count
            record.activity_count = activity_count

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

    @api.depends('process_ids.risk_ids.control_ids')
    def _compute_control_stats(self):
        for record in self:
            # ✅ Récupérer les contrôles via les risques (la relation correcte)
            controls = record.process_ids.mapped('risk_ids.control_ids').filtered(lambda c: c.active)
            record.control_count = len(controls)