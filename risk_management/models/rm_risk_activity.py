from odoo import models, fields, api


class RiskActivity(models.Model):
    _name = 'risk.activity'
    _description = 'Risk Activity / Task'
    _order = 'macro_process_id, process_id, sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # =====================================================
    # CHAMPS DE BASE
    # =====================================================

    name = fields.Char(
        string='Activité',
        required=True,
        tracking=True
    )

    code = fields.Char(
        string='Code',
        help='Code unique de l\'activité',
        tracking=True
    )

    sequence = fields.Integer(
        string='Séquence',
        default=10
    )

    description = fields.Html(
        string='Description'
    )

    summary = fields.Char(
        string='Résumé'
    )

    icon = fields.Char(string='Icône', default='fa-tasks')

    user_id = fields.Many2one(
        'res.users',
        string='Utilisateur responsable',
        tracking=True
    )

    # =====================================================
    # RELATIONS HIÉRARCHIQUES
    # =====================================================

    macro_process_id = fields.Many2one(
        'risk.macro.process',
        string='Macro Processus',
        related='process_id.macro_process_id',
        store=True
    )

    process_id = fields.Many2one(
        'risk.process',
        string='Processus',
        required=True,
        tracking=True
    )

    owner_id = fields.Many2one(
        'hr.employee',
        string='Responsable',
        tracking=True
    )

    # =====================================================
    # RELATIONS AVEC LES RISQUES
    # =====================================================

    risk_ids = fields.One2many(
        'risk.risk',
        'activity_id',
        string='Risques'
    )

    date_deadline = fields.Date(
        string='Date limite',
        help='Date limite de réalisation de l\'activité'
    )

    # Date de début
    date_start = fields.Date(
        string='Date de début',
        help='Date de début de l\'activité'
    )

    # Date de fin
    date_end = fields.Date(
        string='Date de fin',
        help='Date de fin de l\'activité'
    )

    # =====================================================
    # CHAMPS STATISTIQUES
    # =====================================================

    risk_count = fields.Integer(
        compute='_compute_stats',
        string='Nombre de risques',
        store=True
    )

    # ⬇️ CHAMP CALCULÉ (basé sur les risques liés) ⬇️
    risk_level = fields.Selection(
        [
            ('1', 'Très faible'),
            ('2', 'Faible'),
            ('3', 'Moyen'),
            ('4', 'Élevé'),
            ('5', 'Critique')
        ],
        compute='_compute_stats',
        string='Niveau de risque',
        store=True,
        help='Niveau de risque maximum parmi les risques associés à cette activité'
    )

    critical_risk_count = fields.Integer(
        compute='_compute_stats',
        string='Risques critiques',
        store=True
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

    calendar_event_id = fields.Many2one(
        'calendar.event',
        string="Événement calendrier",
        help="Événement calendrier lié à cette activité",
        tracking=True,
        copy=False
    )

    def action_activate(self):
        for record in self:
            record.state = 'active'

    def action_archive(self):
        for record in self:
            record.state = 'archived'

    def action_draft(self):
        for record in self:
            record.state = 'draft'

    # =====================================================
    # MÉTHODES DE CALCUL
    # =====================================================

    @api.depends('risk_ids', 'risk_ids.risk_level')
    def _compute_stats(self):
        """Calcule les statistiques basées sur les risques liés"""
        for record in self:
            # Nombre de risques
            record.risk_count = len(record.risk_ids)

            # Niveau de risque maximum
            max_level = 0
            critical_count = 0

            for risk in record.risk_ids:
                # Récupère le niveau de risque (à adapter selon votre modèle risk.risk)
                if hasattr(risk, 'risk_level'):
                    level = int(risk.risk_level) if risk.risk_level else 1
                elif hasattr(risk, 'inherent_risk'):
                    level = int(risk.inherent_risk) if risk.inherent_risk else 1
                else:
                    level = 1

                if level > max_level:
                    max_level = level

                # Compte les risques critiques (niveau 4 ou 5)
                if level >= 4:
                    critical_count += 1

            # Met à jour le niveau (1 par défaut si aucun risque)
            record.risk_level = str(max_level) if max_level > 0 else '1'
            record.critical_risk_count = critical_count

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_view_risks(self):
        """Ouvre la vue des risques liés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Risques',
            'res_model': 'risk.risk',
            'view_mode': 'tree,form',
            'domain': [('activity_id', '=', self.id)],
            'context': {'default_activity_id': self.id},
        }

    # =====================================================
    # MÉTHODE DE CRÉATION
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.activity')
        return super().create(vals_list)