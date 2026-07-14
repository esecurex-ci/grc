# models/risk_process.py

from odoo import models, fields, api


class RiskProcess(models.Model):
    _name = 'risk.process'
    _description = 'Processus'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category, name'

    name = fields.Char(string='Nom du processus', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)

    category = fields.Selection([
        ('pilotage', 'Processus de Pilotage'),
        ('operational', 'Processus Opérationnels'),
        ('support', 'Processus Supports'),
    ], string='Catégorie', required=True, default='operational', tracking=True)

    macro_process_id = fields.Many2one('risk.macro.process', string='Famille', tracking=True)
    description = fields.Text(string='Description')
    owner_id = fields.Many2one('hr.employee', string='Propriétaire', tracking=True)
    active = fields.Boolean(default=True)

    # Relation inverse vers les risques
    risk_ids = fields.One2many('risk.risk', 'process_id', string='Risques associés')

    # ✅ Même échelle que risk.risk
    risk_level = fields.Selection([
        ('1', 'Très faible'),
        ('2', 'Faible'),
        ('3', 'Moyen'),
        ('4', 'Élevé'),
        ('5', 'Critique')
    ],
        compute='_compute_risk_stats',
        store=True,
        string='Niveau de risque')

    count_risk = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Nombre de risques"
    )

    critical_risk_count = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Risques critiques"
    )

    high_risk_count = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Risques élevés"
    )

    medium_risk_count = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Risques moyens"
    )

    low_risk_count = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Risques faibles"
    )

    activity_ids = fields.One2many(
        'risk.activity',
        'process_id',
        string='Activités'
    )

    activity_count = fields.Integer(
        compute='_compute_activity_count',
        store=True,
        string="Nombre d'activités"
    )

    activity_type_icon = fields.Char(
        compute='_compute_activity_type_icon',
        string='Icône',
        store=False
    )

    state = fields.Selection([
        ('draft', '📝 Brouillon'),
        ('mapped', '🗺️ Cartographié'),
        ('analyzed', '📊 Analysé'),
        ('validated', '✅ Validé'),
        ('active', '🔄 Actif'),
        ('review', '🔍 En révision'),
        ('obsolete', '📦 Obsolète'),
    ], string='Statut', default='draft', tracking=True, index=True)

    maturity_level = fields.Selection([
        ('1', '🌟 Initial'),
        ('2', '📐 Répétable'),
        ('3', '📋 Défini'),
        ('4', '📊 Géré'),
        ('5', '🏆 Optimisé'),
    ], string='Niveau de maturité', default='1', tracking=True)

    maturity_score = fields.Float(
        compute='_compute_maturity_score',
        string='Score de maturité (%)'
    )

    activity_summary = fields.Char(related='activity_ids.summary', string='Résumé')

    validation_date = fields.Date(
        string='Date de validation',
        tracking=True,
        help="Date à laquelle le processus a été validé"
    )

    validation_user_id = fields.Many2one(
        'res.users',
        string='Validé par',
        tracking=True,
        help="Utilisateur qui a validé le processus"
    )

    review_date = fields.Date(
        string='Date de révision',
        tracking=True,
        help="Date de la dernière révision du processus"
    )

    next_review_date = fields.Date(
        string='Prochaine révision',
        tracking=True,
        help="Date prévue pour la prochaine révision"
    )

    review_frequency = fields.Selection([
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('semiannual', 'Semestrielle'),
        ('annual', 'Annuelle'),
        ('biennial', 'Bisanuelle'),
    ], string='Fréquence de révision', default='annual', tracking=True)

    @api.depends('activity_ids')
    def _compute_activity_count(self):
        for record in self:
            record.activity_count = len(record.activity_ids)

    @api.depends('activity_ids', 'activity_ids.risk_ids', 'activity_ids.risk_ids.active')
    def _compute_risk_ids(self):
        """Récupère tous les risques des activités liées à ce processus"""
        for record in self:
            risks = record.activity_ids.mapped('risk_ids').filtered(lambda r: r.active)
            record.risk_ids = [(6, 0, risks.ids)]

    @api.depends('activity_ids', 'activity_ids.risk_ids', 'activity_ids.risk_ids.risk_level',
                 'activity_ids.risk_ids.active')
    def _compute_risk_stats(self):
        for record in self:
            risks = record.activity_ids.mapped('risk_ids').filtered(lambda r: r.active)

            record.count_risk = len(risks)
            record.critical_risk_count = len(risks.filtered(lambda r: r.risk_level == '5'))
            record.high_risk_count = len(risks.filtered(lambda r: r.risk_level == '4'))
            record.medium_risk_count = len(risks.filtered(lambda r: r.risk_level == '3'))
            record.low_risk_count = len(risks.filtered(lambda r: r.risk_level in ['1', '2']))

            max_level = 1
            for risk in risks:
                level = int(risk.risk_level or 1)
                if level > max_level:
                    max_level = level
            record.risk_level = str(max_level)

    def action_view_risks(self):
        """Ouvre la liste complète des risques associés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Risques - {self.name}',
            'res_model': 'risk.risk',
            'view_mode': 'list,form,kanban',
            'domain': [('activity_id.process_id', '=', self.id)],
            'context': {'default_process_id': self.id},
        }

    @api.depends('state', 'count_risk', 'critical_risk_count', 'activity_count')
    def _compute_maturity_score(self):
        for record in self:
            score = 0

            # Niveau de cartographie (20%)
            if record.state not in ['draft', 'obsolete']:
                score += 20

            # Risques analysés (30%)
            if record.count_risk > 0:
                ratio = record.critical_risk_count / record.count_risk
                score += (1 - ratio) * 30

            # Activités définies (25%)
            if record.activity_count > 0:
                score += 25

            # Statut actif (25%)
            if record.state == 'active':
                score += 25

            record.maturity_score = round(score, 1)

    def action_add_risk(self):
        """Ouvre la vue de création d'un risque lié au processus"""
        self.ensure_one()
        activity = self.activity_ids[:1]
        if not activity:
            activity = self.env['risk.activity'].create({
                'name': f'Activité principale - {self.name}',
                'process_id': self.id,
                'owner_id': self.owner_id.id,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': f'Ajouter un risque - {self.name}',
            'res_model': 'risk.risk',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_activity_id': activity.id,
                'default_process_id': self.id,
            },
        }

    def get_risk_stats(self):
        """Retourne les statistiques des risques associés"""
        self.ensure_one()
        risks = self.risk_ids.filtered(lambda r: r.active)
        return {
            'total': len(risks),
            'critical': len(risks.filtered(lambda r: r.risk_level == '5')),
            'high': len(risks.filtered(lambda r: r.risk_level == '4')),
            'medium': len(risks.filtered(lambda r: r.risk_level == '3')),
            'low': len(risks.filtered(lambda r: r.risk_level in ['1', '2'])),
        }

    def action_view_activities(self):
        """Ouvre la liste complète des activités du processus"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Activités - {self.name}',
            'res_model': 'risk.activity',
            'view_mode': 'list,form,kanban',
            'domain': [('process_id', '=', self.id)],
            'context': {'default_process_id': self.id},
        }

    def action_add_activity(self):
        """Ouvre la vue de création d'une activité liée au processus"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ajouter une activité - {self.name}',
            'res_model': 'risk.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_process_id': self.id,
            },
        }

    @api.depends('category')
    def _compute_activity_type_icon(self):
        icons = {
            'pilotage': 'fa-flag',
            'operational': 'fa-cogs',
            'support': 'fa-life-ring',
        }
        for record in self:
            record.activity_type_icon = icons.get(record.category, 'fa-tasks')

    def action_map(self):
        """Cartographier le processus"""
        self.ensure_one()
        self.state = 'mapped'
        return True

    def action_analyze(self):
        """Analyser le processus"""
        self.ensure_one()
        self.state = 'analyzed'
        return True

    def action_validate(self):
        """Valider le processus"""
        self.ensure_one()
        self.state = 'validated'
        return True

    def action_activate(self):
        """Activer le processus"""
        self.ensure_one()
        self.state = 'active'
        return True

    def action_review(self):
        """Mettre en révision"""
        self.ensure_one()
        self.state = 'review'
        return True

    def action_obsolete(self):
        """Rendre obsolète"""
        self.ensure_one()
        self.state = 'obsolete'
        self.active = False
        return True

    def action_reset_to_draft(self):
        """Remettre en brouillon"""
        self.ensure_one()
        self.state = 'draft'
        return True

    @api.constrains('state')
    def _check_state_transition(self):
        """Vérifie les transitions d'état valides"""
        valid_transitions = {
            'draft': ['mapped'],
            'mapped': ['analyzed', 'obsolete'],
            'analyzed': ['validated', 'obsolete'],
            'validated': ['active', 'obsolete'],
            'active': ['review', 'obsolete'],
            'review': ['active', 'validated', 'obsolete'],
            'obsolete': [],
        }
        for record in self:
            if hasattr(record, '_origin_state'):
                if record.state not in valid_transitions.get(record._origin_state, []):
                    raise ValidationError(
                        _("Transition d'état invalide: %s → %s") %
                        (record._origin_state, record.state)
                    )

    def action_validate(self):
        """Valider le processus"""
        self.ensure_one()
        self.state = 'validated'
        self.validation_date = fields.Date.today()
        self.validation_user_id = self.env.user
        return True

    def action_review(self):
        """Mettre en révision"""
        self.ensure_one()
        self.state = 'review'
        self.review_date = fields.Date.today()
        return True

    def action_activate(self):
        """Activer le processus"""
        self.ensure_one()
        self.state = 'active'
        return True