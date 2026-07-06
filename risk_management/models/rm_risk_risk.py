from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class RiskRisk(models.Model):
    _name = 'risk.risk'
    _description = 'Risque'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Risque', tracking=True)
    code = fields.Char(string='Code', readonly=True, default='New', tracking=True)
    description = fields.Html(string='Description')
    cause_description = fields.Html(string='Cause')
    consequence_description = fields.Html(string='Conséquence')
    category_id = fields.Many2one('risk.category', string='Catégorie', tracking=True,
                                  default=lambda self: self._get_default_category())

    @api.model
    def _get_default_category(self):
        """Retourne une catégorie par défaut"""
        category = self.env['risk.category'].search([], limit=1)
        return category.id if category else False

    subcategory_id = fields.Many2one('risk.subcategory', string='Sous-catégorie', tracking=True)
    owner_id = fields.Many2one('hr.employee', string='Propriétaire du risque', tracking=True)
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    appetite = fields.Selection([
        ('very_low', 'Très faible'),
        ('low', 'Faible'),
        ('medium', 'Moyen'),
        ('high', 'Élevé'),
        ('critical', 'Critique'),
    ], string='Appétit au risque', default='medium')
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('validated', 'Validé'),
        ('obsolete', 'Obsolète')
    ], string='Statut', default='draft', tracking=True)
    cause_ids = fields.Many2many('risk.cause', string='Causes')
    impact_ids = fields.Many2many('risk.impact', string='Impacts')
    regulation_ids = fields.Many2many('risk.regulation', string='Réglementations')
    asset_ids = fields.Many2many('risk.asset', string='Actifs')
    organization_ids = fields.Many2many('risk.organization', string='Unités organisationnelles')
    active = fields.Boolean(string='Actif', default=True)
    control_ids = fields.Many2many('risk.control', string='Contrôles')
    kri_ids = fields.Many2many('risk.kri', string='KRI')
    incident_ids = fields.One2many('risk.incident', 'risk_id', string='Incidents')
    incident_count = fields.Integer(compute='_compute_incident_count', string="Nombre d'incidents")
    total_loss_amount = fields.Monetary(compute='_compute_total_loss', string='Montant total des pertes')
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)
    audit_finding_ids = fields.One2many('risk.audit.finding', 'risk_id', string='Constats d\'audit')
    audit_finding_count = fields.Integer(compute='_compute_audit_finding_count', string="Nombre de constats d'audit")
    compliance_requirement_ids = fields.Many2many('risk.compliance.requirement', string='Exigences de conformité')

    # ============================================================
    # CHAMPS D'ÉCHELLE AVEC SÉLECTIONS DYNAMIQUES
    # ============================================================

    inherent_probability = fields.Selection(
        selection='_get_probability_selection',
        string='Probabilité inhérente',
        default='3'
    )
    inherent_impact = fields.Selection(
        selection='_get_impact_selection',
        string='Impact inhérent',
        default='3'
    )
    inherent_score = fields.Integer(compute='_compute_scores', store=True, string='Score inhérent')
    inherent_level = fields.Selection(
        selection='_get_level_selection',
        compute='_compute_scores',
        store=True,
        string='Niveau inhérent'
    )
    residual_probability = fields.Selection(
        selection='_get_probability_selection',
        string='Probabilité résiduelle',
        default='3'
    )
    residual_impact = fields.Selection(
        selection='_get_impact_selection',
        string='Impact résiduel',
        default='3'
    )
    residual_score = fields.Integer(compute='_compute_scores', store=True, string='Score résiduel')
    residual_level = fields.Selection(
        selection='_get_level_selection',
        compute='_compute_scores',
        store=True,
        string='Niveau résiduel'
    )

    review_frequency = fields.Selection([
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('semiannual', 'Semestrielle'),
        ('annual', 'Annuelle')
    ], string='Fréquence de révision', default='quarterly', tracking=True)
    last_review_date = fields.Date(string='Date de dernière révision', tracking=True)
    next_review_date = fields.Date(compute='_compute_next_review_date', store=True, tracking=True,
                                   string='Prochaine révision')
    review_overdue = fields.Boolean(compute='_compute_review_overdue', store=True, string='Révision en retard')
    risk_type = fields.Selection([
        ('strategic', 'Stratégique'),
        ('operational', 'Opérationnel'),
        ('financial', 'Financier'),
        ('compliance', 'Conformité'),
        ('cyber', 'Cybersécurité'),
        ('reputation', 'Réputation'),
        ('liquidity', 'Liquidité'),
        ('market', 'Marché'),
        ('contreparty', 'Contrepartie')
    ], string='Type de risque', tracking=True)
    risk_source = fields.Selection([
        ('internal', 'Interne'),
        ('external', 'Externe'),
        ('regulatory', 'Réglementaire'),
        ('technology', 'Technologique'),
        ('human', 'Humain'),
        ('supplier', 'Fournisseur')
    ], string='Source du risque', tracking=True)
    cause = fields.Html(string='Cause')
    risk_event = fields.Html(string='Événement redouté')
    consequence = fields.Html(string='Conséquence')
    existing_control = fields.Html(string='Contrôles existants')
    assessment_ids = fields.One2many('risk.assessment', 'risk_id', string='Évaluations')
    activity_id = fields.Many2one('risk.activity', string='Activité', ondelete='set null', tracking=True,
                                  help='Activité concernée par ce risque')
    process_id = fields.Many2one('risk.process', related='activity_id.process_id', store=True, string='Processus')
    risk_level = fields.Selection([
        ('1', 'Très faible'),
        ('2', 'Faible'),
        ('3', 'Moyen'),
        ('4', 'Élevé'),
        ('5', 'Critique')
    ], string='Niveau de risque', default='1', help='Niveau de risque (1 = Très faible, 5 = Critique)', store=True)
    macro_process_id = fields.Many2one('risk.macro.process', related='activity_id.macro_process_id', store=True,
                                       string='Macro-processus')
    last_assessment_id = fields.Many2one('risk.assessment', compute='_compute_last_assessment', compute_sudo=True,
                                         store=True, string='Dernière évaluation')
    last_assessment_date = fields.Date(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                       string='Date de la dernière évaluation')
    last_inherent_score = fields.Integer(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                         string='Score inhérent (dernière éval.)')
    last_residual_score = fields.Integer(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                         string='Score résiduel (dernière éval.)')
    process_category = fields.Selection([
        ('pilotage', 'Processus de Pilotage'),
        ('operational', 'Processus Opérationnels'),
        ('support', 'Processus Supports'),
    ], string='Catégorie de processus', related='process_id.category', store=True)

    last_risk_level = fields.Selection(
        selection='_get_level_selection',
        compute='_compute_last_assessment',
        compute_sudo=True,
        store=True,
        string='Niveau de risque (dernière éval.)'
    )
    last_over_appetite = fields.Boolean(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                        string='Hors appétit (dernière éval.)')
    last_inherent_probability = fields.Integer(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                               string='Probabilité inhérente (dernière éval.)')
    last_inherent_impact = fields.Integer(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                          string='Impact inhérent (dernière éval.)')
    assessment_count = fields.Integer(compute='_compute_assessment_count', compute_sudo=True, store=True,
                                      string="Nombre d'évaluations")

    # Champs pour la matrice
    impact_value = fields.Integer(compute='_compute_impact_values', store=True, string='Valeur de l\'impact')
    probability_value = fields.Integer(compute='_compute_impact_values', store=True, string='Valeur de la probabilité')
    matrix_html = fields.Html(compute='_compute_matrix_html', string='Position du risque', sanitize=False, store=False)

    # Relations DMR
    dmr_control_ids = fields.Many2many(
        'risk.control',
        'risk_risk_dmr_control_rel',
        'risk_id',
        'control_id',
        string='Contrôles du DMR',
        help="Contrôles internes mis en place pour maîtriser ce risque"
    )

    dmr_test_ids = fields.Many2many(
        'risk.control.test',
        'risk_risk_dmr_test_rel',
        'risk_id',
        'test_id',
        string='Tests du DMR',
        help="Tests de contrôle effectués pour ce risque"
    )

    dmr_action_ids = fields.Many2many(
        'risk.corrective.action',
        'risk_risk_dmr_action_rel',
        'risk_id',
        'action_id',
        string='Actions du DMR',
        help="Actions correctives liées à ce risque"
    )

    dmr_kri_ids = fields.Many2many(
        'risk.kri',
        'risk_risk_dmr_kri_rel',
        'risk_id',
        'kri_id',
        string='KRI du DMR',
        help="KRI associés à ce risque"
    )

    # ============================================================
    # STATISTIQUES DMR
    # ============================================================

    dmr_control_count = fields.Integer(
        compute='_compute_dmr_stats',
        string="Nombre de contrôles"
    )

    dmr_effective_control_count = fields.Integer(
        compute='_compute_dmr_stats',
        string="Contrôles efficaces"
    )

    dmr_control_effectiveness_rate = fields.Float(
        compute='_compute_dmr_stats',
        string="Taux d'efficacité des contrôles (%)"
    )

    dmr_test_count = fields.Integer(
        compute='_compute_dmr_stats',
        string="Nombre de tests"
    )

    dmr_test_pass_rate = fields.Float(
        compute='_compute_dmr_stats',
        string="Taux de réussite des tests (%)"
    )

    dmr_compliance_score = fields.Float(
        compute='_compute_dmr_stats',
        string="Score de conformité DMR (%)",
        help="Score global du dispositif de maîtrise"
    )

    dmr_status = fields.Selection([
        ('strong', '🟢 Fort'),
        ('adequate', '🟡 Adéquat'),
        ('weak', '🟠 Faible'),
        ('critical', '🔴 Critique'),
    ], compute='_compute_dmr_stats', string="Niveau de maîtrise")

    test_ids = fields.Many2many(
        'risk.control.test',
        'risk_risk_test_rel',
        'risk_id',
        'test_id',
        string='Tests de contrôle',
        help="Tests de contrôle associés à ce risque"
    )

    action_ids = fields.Many2many(
        'risk.corrective.action',
        'risk_risk_action_rel',
        'risk_id',
        'action_id',
        string='Actions correctives',
        help="Actions correctives associées à ce risque"
    )

    # ✅ Champs DMR complets
    dmr_control_ids = fields.Many2many(
        'risk.control',
        'risk_risk_dmr_control_rel',
        'risk_id',
        'control_id',
        string='Contrôles du DMR'
    )

    dmr_action_count = fields.Integer(
        compute='_compute_dmr_stats',
        string="Nombre de plans d'action"
    )

    dmr_action_progress = fields.Float(
        compute='_compute_dmr_stats',
        string="Progression des plans d'action (%)"
    )

    action_plan_ids = fields.Many2many(
        'risk.action.plan',
        'risk_risk_action_plan_rel',
        'risk_id',
        'action_plan_id',
        string='Plans d\'action',
        help="Plans d'action associés à ce risque"
    )

    # ============================================================
    # COMPUTE DMR
    # ============================================================

    @api.depends(
        'control_ids', 'control_ids.effectiveness',
        'test_ids', 'test_ids.result',
        'action_plan_ids', 'action_plan_ids.task_progress'
    )
    def _compute_dmr_stats(self):
        for record in self:
            # 1. CONTRÔLES
            controls = record.dmr_control_ids
            record.dmr_control_count = len(controls)

            effective = len(controls.filtered(
                lambda c: c.effectiveness in ['high', 'medium']
            ))
            record.dmr_effective_control_count = effective

            if record.dmr_control_count > 0:
                record.dmr_control_effectiveness_rate = (
                        (effective / record.dmr_control_count) * 100
                )
            else:
                record.dmr_control_effectiveness_rate = 0

            # 2. TESTS
            tests = record.dmr_test_ids
            record.dmr_test_count = len(tests)

            passed = len(tests.filtered(lambda t: t.result == 'pass'))
            if record.dmr_test_count > 0:
                record.dmr_test_pass_rate = (passed / record.dmr_test_count) * 100
            else:
                record.dmr_test_pass_rate = 0

            # 3. ACTIONS
            action_plans = record.action_plan_ids
            record.dmr_action_count = len(action_plans)

            if record.dmr_action_count > 0:
                progress_sum = sum(action_plans.mapped('task_progress'))
                record.dmr_action_progress = progress_sum / record.dmr_action_count
            else:
                record.dmr_action_progress = 0

            # 4. SCORE GLOBAL
            # Pondération : Contrôles (40%), Tests (30%), Actions (30%)
            weight_controls = 0.4
            weight_tests = 0.3
            weight_actions = 0.3

            score = (
                    record.dmr_control_effectiveness_rate * weight_controls +
                    record.dmr_test_pass_rate * weight_tests +
                    record.dmr_action_progress * weight_actions
            )
            record.dmr_compliance_score = round(score, 1)

            # 5. NIVEAU DE MAÎTRISE
            if record.dmr_compliance_score >= 80:
                record.dmr_status = 'strong'
            elif record.dmr_compliance_score >= 60:
                record.dmr_status = 'adequate'
            elif record.dmr_compliance_score >= 40:
                record.dmr_status = 'weak'
            else:
                record.dmr_status = 'critical'

    # ============================================================
    # MÉTHODES D'ACTION DMR
    # ============================================================

    def action_view_dmr_controls(self):
        """Voir les contrôles du DMR"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Contrôles DMR - {self.name}',
            'res_model': 'risk.control',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', self.dmr_control_ids.ids)],
        }

    def action_view_dmr_tests(self):
        """Voir les tests du DMR"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Tests DMR - {self.name}',
            'res_model': 'risk.control.test',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.dmr_test_ids.ids)],
        }

    def action_view_dmr_actions(self):
        """Voir les actions du DMR"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Actions DMR - {self.name}',
            'res_model': 'risk.corrective.action',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', self.dmr_action_ids.ids)],
        }

    def action_view_dmr_kris(self):
        """Voir les KRI du DMR"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'KRI DMR - {self.name}',
            'res_model': 'risk.kri',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.dmr_kri_ids.ids)],
        }

    # ============================================================
    # MÉTHODES POUR LES ÉCHELLES CONFIGURÉES
    # ============================================================

    @api.model
    def _get_scale_config(self):
        """Récupère la configuration des échelles"""
        config = self.env['risk.config.settings'].search([], limit=1)
        if not config:
            # Créer une configuration par défaut si elle n'existe pas
            config = self.env['risk.config.settings'].create({})
            # Charger les valeurs par défaut
            prob_values = self.env['risk.scale.value'].search([
                ('scale_type', '=', 'probability'),
                ('active', '=', True)
            ])
            impact_values = self.env['risk.scale.value'].search([
                ('scale_type', '=', 'impact'),
                ('active', '=', True)
            ])
            level_values = self.env['risk.scale.value'].search([
                ('scale_type', '=', 'level'),
                ('active', '=', True)
            ])
            if prob_values and impact_values and level_values:
                config.write({
                    'scale_probability_ids': [(6, 0, prob_values.ids)],
                    'scale_impact_ids': [(6, 0, impact_values.ids)],
                    'scale_level_ids': [(6, 0, level_values.ids)],
                })
        return config

    @api.model
    def _get_probability_scale(self):
        """Récupère l'échelle de probabilité configurée"""
        try:
            config = self._get_scale_config()
            if config and config.scale_probability_ids:
                return config.scale_probability_ids.sorted('sequence')
        except Exception:
            pass
        return self.env['risk.scale.value']

    @api.model
    def _get_impact_scale(self):
        """Récupère l'échelle d'impact configurée"""
        try:
            config = self._get_scale_config()
            if config and config.scale_impact_ids:
                return config.scale_impact_ids.sorted('sequence')
        except Exception:
            pass
        return self.env['risk.scale.value']

    @api.model
    def _get_level_scale(self):
        """Récupère l'échelle des niveaux configurée"""
        try:
            config = self._get_scale_config()
            if config and config.scale_level_ids:
                return config.scale_level_ids.sorted('sequence')
        except Exception:
            pass
        return self.env['risk.scale.value']

    @api.model
    def _get_probability_selection(self):
        """Retourne la sélection pour le champ inherent_probability"""
        try:
            scale = self._get_probability_scale()
            if scale:
                return [(str(record.numeric_value if record.numeric_value else record.value), record.name)
                        for record in scale if record.active]
        except Exception:
            pass
        # Valeurs par défaut si aucune donnée n'existe ou erreur
        return [
            ('1', 'Très faible'),
            ('2', 'Faible'),
            ('3', 'Moyen'),
            ('4', 'Élevé'),
            ('5', 'Très élevé'),
        ]

    @api.model
    def _get_impact_selection(self):
        """Retourne la sélection pour le champ inherent_impact"""
        try:
            scale = self._get_impact_scale()
            if scale:
                return [(str(record.numeric_value if record.numeric_value else record.value), record.name)
                        for record in scale if record.active]
        except Exception:
            pass
        # Valeurs par défaut si aucune donnée n'existe ou erreur
        return [
            ('1', 'Insignifiant'),
            ('2', 'Mineur'),
            ('3', 'Modéré'),
            ('4', 'Majeur'),
            ('5', 'Catastrophique'),
        ]

    @api.model
    def _get_level_selection(self):
        """Retourne la sélection pour le champ inherent_level"""
        try:
            scale = self._get_level_scale()
            if scale:
                return [(record.value, record.name) for record in scale if record.active]
        except Exception:
            pass
        # Valeurs par défaut si aucune donnée n'existe ou erreur
        return [
            ('low', 'Faible'),
            ('medium', 'Moyen'),
            ('high', 'Élevé'),
            ('critical', 'Critique'),
        ]

    @api.depends('last_review_date', 'review_frequency')
    def _compute_next_review_date(self):
        for rec in self:
            rec.next_review_date = False
            if not rec.last_review_date:
                continue
            if rec.review_frequency == 'monthly':
                rec.next_review_date = rec.last_review_date + relativedelta(months=1)
            elif rec.review_frequency == 'quarterly':
                rec.next_review_date = rec.last_review_date + relativedelta(months=3)
            elif rec.review_frequency == 'semiannual':
                rec.next_review_date = rec.last_review_date + relativedelta(months=6)
            elif rec.review_frequency == 'annual':
                rec.next_review_date = rec.last_review_date + relativedelta(years=1)

    @api.depends('next_review_date')
    def _compute_review_overdue(self):
        today = fields.Date.today()
        for rec in self:
            rec.review_overdue = bool(rec.next_review_date and rec.next_review_date < today)

    # ============================================================
    # CALCUL DES SCORES AVEC ÉCHELLES CONFIGURÉES
    # ============================================================

    @api.depends('inherent_probability', 'inherent_impact', 'residual_probability', 'residual_impact')
    def _compute_scores(self):
        for rec in self:
            # Récupérer les valeurs numériques
            prob_value = int(rec.inherent_probability or 3)
            impact_value = int(rec.inherent_impact or 3)

            # Score inhérent
            inherent = prob_value * impact_value
            rec.inherent_score = inherent

            # Score résiduel
            residual_prob = int(rec.residual_probability or 3)
            residual_imp = int(rec.residual_impact or 3)
            residual = residual_prob * residual_imp
            rec.residual_score = residual

            # Déterminer les niveaux avec l'échelle configurée
            rec.inherent_level = rec._get_level_from_score(inherent)
            rec.residual_level = rec._get_level_from_score(residual)

    def _get_level_from_score(self, score):
        """Détermine le niveau à partir du score en utilisant l'échelle configurée"""
        try:
            level_scale = self._get_level_scale()
            for level in level_scale:
                if level.score_min <= score <= level.score_max:
                    return level.value
        except Exception:
            pass
        # Valeurs par défaut si l'échelle n'est pas disponible
        if score <= 5:
            return 'low'
        if score <= 10:
            return 'medium'
        if score <= 15:
            return 'high'
        return 'critical'

    # Méthode de fallback pour la compatibilité
    def _get_level(self, score):
        """Méthode de fallback (gardée pour compatibilité)"""
        return self._get_level_from_score(score)

    @api.depends('audit_finding_ids')
    def _compute_audit_finding_count(self):
        for rec in self:
            rec.audit_finding_count = len(rec.audit_finding_ids)

    @api.depends('incident_ids')
    def _compute_incident_count(self):
        for rec in self:
            rec.incident_count = len(rec.incident_ids)

    @api.depends('incident_ids.total_loss')
    def _compute_total_loss(self):
        for rec in self:
            rec.total_loss_amount = sum(rec.incident_ids.mapped('total_loss'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.risk')
        return super().create(vals_list)

    def action_assess(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Évaluation du risque',
            'res_model': 'risk.assessment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_risk_id': self.id,
            },
        }

    def action_close(self):
        for record in self:
            record.state = 'obsolete'
            record.active = False
        return True

    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        if self.activity_id:
            self.process_id = self.activity_id.process_id
            self.macro_process_id = self.activity_id.macro_process_id

    # ============================================================
    # MÉTHODE POUR LA MATRICE
    # ============================================================

    def get_matrix_color(self, score):
        if score <= 4:
            return 'bg-success'
        elif score <= 9:
            return 'bg-warning'
        elif score <= 16:
            return 'bg-orange'
        else:
            return 'bg-danger'

    def get_risk_distribution(self):
        levels = {
            'low': 0,
            'moderate': 0,
            'important': 0,
            'high': 0,
            'critical': 0
        }
        for risk in self.search([('active', '=', True)]):
            level = risk.last_risk_level or 'low'
            if level in levels:
                levels[level] += 1
        return levels

    # ============================================================
    # _compute_last_assessment
    # ============================================================

    @api.depends('assessment_ids', 'assessment_ids.assessment_date')
    def _compute_last_assessment(self):
        for risk in self:
            last = risk.assessment_ids.sorted(
                key=lambda r: r.assessment_date or r.create_date,
                reverse=True
            )[:1]
            if last:
                risk.last_assessment_id = last.id
                risk.last_assessment_date = last.assessment_date
                risk.last_inherent_score = last.inherent_score
                risk.last_residual_score = last.residual_score
                risk.last_risk_level = last.risk_level
                risk.last_over_appetite = last.over_appetite
                risk.last_inherent_probability = last.inherent_probability
                risk.last_inherent_impact = last.inherent_impact
            else:
                risk.last_assessment_id = False
                risk.last_assessment_date = False
                risk.last_inherent_score = 0
                risk.last_residual_score = 0
                risk.last_risk_level = False
                risk.last_over_appetite = False
                risk.last_inherent_probability = 0
                risk.last_inherent_impact = 0

    @api.depends('assessment_ids')
    def _compute_assessment_count(self):
        for risk in self:
            risk.assessment_count = len(risk.assessment_ids)

    @api.depends('inherent_impact', 'inherent_probability')
    def _compute_impact_values(self):
        impact_map = {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            'insignificant': 1, 'minor': 2, 'moderate': 3, 'major': 4, 'catastrophic': 5
        }
        prob_map = {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            'very_low': 1, 'low': 2, 'medium': 3, 'high': 4, 'very_high': 5
        }
        for record in self:
            record.impact_value = impact_map.get(record.inherent_impact, 1)
            record.probability_value = prob_map.get(record.inherent_probability, 1)

    @api.depends(
        'inherent_impact',
        'inherent_probability',
        'inherent_score',
        'inherent_level',
        'residual_impact',
        'residual_probability',
        'residual_score',
        'residual_level'
    )
    def _compute_matrix_html(self):
        for record in self:
            try:
                impact = int(record.inherent_impact or 1)
                probability = int(record.inherent_probability or 1)
                score = record.inherent_score or 0
                level = record.inherent_level or 'non défini'
                residual_score = record.residual_score or 0
                residual_level = record.residual_level or 'non défini'

                html = f'''
                <div class="risk-matrix-wrapper" style="width:100%;max-width:750px;margin:0 auto;padding:20px;background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                    <h3 style="text-align:center;font-size:22px;font-weight:700;color:#1a237e;margin-bottom:20px;padding-bottom:12px;border-bottom:3px solid #e8eaf6;">📊 Position du risque</h3>

                    <table style="width:100%;border-collapse:collapse;margin:10px 0;border:1px solid #dee2e6;">
                        <thead>
                            <tr>
                                <th style="background:#f5f5f5;font-weight:700;color:#37474f;border:1px solid #dee2e6;padding:12px 16px;text-align:center;min-width:80px;">Probabilité ↓</th>
                '''

                for i in range(1, 6):
                    html += f'<th style="background:#f5f5f5;font-weight:700;color:#37474f;border:1px solid #dee2e6;padding:12px 16px;text-align:center;min-width:50px;">{i}</th>'
                html += '''
                            </tr>
                        </thead>
                        <tbody>
                '''

                for prob in range(5, 0, -1):
                    html += f'<tr><td style="background:#f5f5f5;font-weight:700;color:#37474f;border:1px solid #dee2e6;padding:12px 16px;text-align:center;min-width:80px;">{prob}</td>'
                    for imp in range(1, 6):
                        score_cell = prob * imp
                        color = record._get_matrix_color(score_cell)
                        is_active = (prob == probability and imp == impact)
                        text_color = 'white' if score_cell > 12 else 'black'
                        active_style = 'border:4px solid #1a237e !important;box-shadow:0 0 0 3px #1a237e;background-color:#ffffff;font-weight:800;transform:scale(1.05);' if is_active else ''
                        html += f'<td style="background-color:{color};color:{text_color};border:1px solid #dee2e6;padding:14px 18px;text-align:center;font-weight:{"800" if is_active else "600"};font-size:16px;cursor:default;transition:all 0.2s ease;{active_style}">{score_cell}</td>'
                    html += '</tr>'

                html += f'''
                        </tbody>
                    </table>

                    <div style="display:flex;justify-content:center;gap:20px;margin:15px 0;flex-wrap:wrap;padding:12px 20px;background:#f8f9fa;border-radius:8px;">
                        <span style="display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#37474f;">
                            <span style="display:inline-block;width:20px;height:20px;border-radius:4px;background:#28a745;border:1px solid #dee2e6;"></span> Faible (1-4)
                        </span>
                        <span style="display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#37474f;">
                            <span style="display:inline-block;width:20px;height:20px;border-radius:4px;background:#ffc107;border:1px solid #dee2e6;"></span> Moyen (5-9)
                        </span>
                        <span style="display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#37474f;">
                            <span style="display:inline-block;width:20px;height:20px;border-radius:4px;background:#fd7e14;border:1px solid #dee2e6;"></span> Élevé (10-16)
                        </span>
                        <span style="display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#37474f;">
                            <span style="display:inline-block;width:20px;height:20px;border-radius:4px;background:#dc3545;border:1px solid #dee2e6;"></span> Critique (17-25)
                        </span>
                    </div>

                    <div style="text-align:center;margin-top:15px;padding:14px;background:#f8f9fa;border-radius:8px;font-size:15px;">
                        <div style="display:flex;justify-content:center;gap:30px;flex-wrap:wrap;">
                            <div>
                                <strong>Score inhérent :</strong>
                                <span style="font-size:20px;font-weight:700;color:#1a237e;">{score}</span>
                                &nbsp;|&nbsp;
                                <strong>Niveau :</strong>
                                <span class="badge-{level.lower() if level else 'non-defini'}">{level.capitalize() if level else 'Non défini'}</span>
                            </div>
                            <div>
                                <strong>Score résiduel :</strong>
                                <span style="font-size:20px;font-weight:700;color:#1a237e;">{residual_score}</span>
                                &nbsp;|&nbsp;
                                <strong>Niveau :</strong>
                                <span class="badge-{residual_level.lower() if residual_level else 'non-defini'}">{residual_level.capitalize() if residual_level else 'Non défini'}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <style>
                    .badge-low {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#d4edda;color:#155724; }}
                    .badge-medium {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#fff3cd;color:#856404; }}
                    .badge-high {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#ffe5cc;color:#853d04; }}
                    .badge-critical {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#f8d7da;color:#721c24; }}
                    .badge-non-defini {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#e2e3e5;color:#383d41; }}
                </style>
                '''

                record.matrix_html = html

            except Exception as e:
                record.matrix_html = f'<div style="color:red;padding:20px;text-align:center;background:#fff5f5;border-radius:8px;">❌ Erreur: {str(e)}</div>'

    def _get_matrix_color(self, score):
        if score <= 4:
            return '#28a745'
        elif score <= 9:
            return '#ffc107'
        elif score <= 16:
            return '#fd7e14'
        else:
            return '#dc3545'

    # Dans rm_risk_risk.py
    graph_impact = fields.Integer(
        compute='_compute_graph_values',
        store=False,
        string='Impact (graphique)'
    )

    graph_probability = fields.Integer(
        compute='_compute_graph_values',
        store=False,
        string='Probabilité (graphique)'
    )

    @api.depends('inherent_impact', 'inherent_probability')
    def _compute_graph_values(self):
        mapping = {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            'insignificant': 1, 'minor': 2, 'moderate': 3, 'major': 4, 'catastrophic': 5
        }
        for record in self:
            record.graph_impact = mapping.get(record.inherent_impact, 1)
            record.graph_probability = mapping.get(record.inherent_probability, 1)

    # ============================================================
    # MÉTHODES POUR LE TABLEAU DE BORD
    # ============================================================

    def get_dashboard_stats(self):
        """Retourne les statistiques pour le tableau de bord"""
        stats = {
            'total': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'total_score': 0,
            'avg_score': 0,
            'total_incidents': 0,
            'total_loss': 0
        }

        risks = self.search([('active', '=', True)])
        stats['total'] = len(risks)

        for risk in risks:
            stats['total_score'] += risk.inherent_score or 0
            if risk.inherent_level == 'critical':
                stats['critical'] += 1
            elif risk.inherent_level == 'high':
                stats['high'] += 1
            elif risk.inherent_level == 'medium':
                stats['medium'] += 1
            elif risk.inherent_level == 'low':
                stats['low'] += 1
            stats['total_incidents'] += risk.incident_count or 0
            stats['total_loss'] += risk.total_loss_amount or 0

        stats['avg_score'] = round(stats['total_score'] / stats['total'], 2) if stats['total'] > 0 else 0

        return stats

    def get_matrix_data(self):
        """Retourne les données pour la matrice 5x5"""
        matrix = {}
        for i in range(1, 6):
            for j in range(1, 6):
                matrix[f"{i}_{j}"] = 0

        risks = self.search([('active', '=', True)])
        for risk in risks:
            impact = int(risk.inherent_impact or 1)
            prob = int(risk.inherent_probability or 1)
            key = f"{prob}_{impact}"
            if key in matrix:
                matrix[key] += 1

        return matrix

    @api.depends('inherent_impact', 'inherent_probability')
    def _compute_pivot_values(self):
        mapping = {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            'insignificant': 1, 'minor': 2, 'moderate': 3, 'major': 4, 'catastrophic': 5
        }
        for record in self:
            record.impact_value = mapping.get(record.inherent_impact, 1)
            record.probability_value = mapping.get(record.inherent_probability, 1)

    def get_heatmap_data(self):
        """Récupère les données pour la carte de chaleur"""
        data = {}
        risks = self.search([('active', '=', True)])
        for risk in risks:
            impact = int(risk.inherent_impact or 1)
            prob = int(risk.inherent_probability or 1)
            key = f"{prob}_{impact}"
            if key not in data:
                data[key] = []
            data[key].append({
                'id': risk.id,
                'name': risk.name,
                'code': risk.code,
                'level': risk.inherent_level,
                'score': risk.inherent_score
            })
        return data

    heatmap_html = fields.Html(
        compute='_compute_heatmap_html',
        string='Carte de chaleur',
        sanitize=False,
        store=False
    )

    @api.depends('inherent_impact', 'inherent_probability', 'inherent_level')
    def _compute_heatmap_html(self):
        """Génère la carte de chaleur en HTML avec statistiques améliorées"""
        # Récupérer tous les risques actifs
        risks = self.search([('active', '=', True)])

        if not risks:
            for record in self:
                record.heatmap_html = '''
                <div style="padding:40px;text-align:center;color:#6c757d;background:#f8f9fa;border-radius:12px;">
                    <i class="fa fa-exclamation-triangle" style="font-size:48px;color:#ffc107;"></i>
                    <h3>Aucun risque actif</h3>
                    <p>Créez votre premier risque pour visualiser la carte de chaleur.</p>
                </div>
                '''
            return

        # Créer la matrice 5x5
        matrix = {}
        for i in range(1, 6):
            for j in range(1, 6):
                matrix[f"{i}_{j}"] = []

        for risk in risks:
            impact = int(risk.inherent_impact or 1)
            prob = int(risk.inherent_probability or 1)
            key = f"{prob}_{impact}"
            if key in matrix:
                matrix[key].append({
                    'id': risk.id,
                    'name': risk.name,
                    'code': risk.code,
                    'level': risk.inherent_level,
                    'score': risk.inherent_score
                })

        # Statistiques
        total = len(risks)
        critical

    dashboard_html = fields.Html(
        compute='_compute_dashboard_html',
        string='Dashboard KPI',
        sanitize=False,
        store=False
    )

    @api.depends('inherent_impact', 'inherent_probability', 'inherent_level', 'assessment_ids')
    def _compute_dashboard_html(self):
        """Génère un dashboard KPI complet en HTML avec heatmap interactive"""

        # === Récupération des données ===
        risks = self.search([('active', '=', True)])
        total_risks = len(risks)

        # Statistiques par niveau
        critical = len([r for r in risks if r.inherent_level == 'critical'])
        high = len([r for r in risks if r.inherent_level == 'high'])
        medium = len([r for r in risks if r.inherent_level == 'medium'])
        low = len([r for r in risks if r.inherent_level == 'low'])

        # Score moyen
        total_score = sum([r.inherent_score or 0 for r in risks])
        avg_score = round(total_score / total_risks, 1) if total_risks > 0 else 0

        # Statistiques par catégorie
        category_stats = {}
        for risk in risks:
            cat = risk.category_id.name or 'Non catégorisé'
            if cat not in category_stats:
                category_stats[cat] = {'count': 0, 'score': 0}
            category_stats[cat]['count'] += 1
            category_stats[cat]['score'] += risk.inherent_score or 0

        # Données pour la heatmap avec survole
        matrix_data = {}
        for i in range(1, 6):
            for j in range(1, 6):
                matrix_data[f"{i}_{j}"] = []

        for risk in risks:
            impact = int(risk.inherent_impact or 1)
            prob = int(risk.inherent_probability or 1)
            key = f"{prob}_{impact}"
            if key in matrix_data:
                matrix_data[key].append({
                    'id': risk.id,
                    'name': risk.name,
                    'code': risk.code,
                    'level': risk.inherent_level,
                    'score': risk.inherent_score
                })

        # Données résiduelles
        residual_matrix = {}
        for i in range(1, 6):
            for j in range(1, 6):
                residual_matrix[f"{i}_{j}"] = 0
        for risk in risks:
            impact = int(risk.residual_impact or 1)
            prob = int(risk.residual_probability or 1)
            key = f"{prob}_{impact}"
            if key in residual_matrix:
                residual_matrix[key] += 1

        # Données des contrôles
        control_stats = {'effective': 0, 'partial': 0, 'ineffective': 0}
        for risk in risks:
            for control in risk.control_ids:
                effectiveness = control.effectiveness or 0
                if effectiveness >= 80:
                    control_stats['effective'] += 1
                elif effectiveness >= 50:
                    control_stats['partial'] += 1
                else:
                    control_stats['ineffective'] += 1

        # ================================================================
        # GÉNÉRATION DU HTML
        # ================================================================

        html = """
            <style>
                .kpi-dashboard {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    padding: 15px;
                    background: #f5f7fa;
                    border-radius: 12px;
                    max-width: 1400px;
                    margin: 0 auto;
                }
                .kpi-dashboard h2 {
                    color: #1a237e;
                    font-size: 22px;
                    font-weight: 700;
                    margin-bottom: 15px;
                    padding-bottom: 8px;
                    border-bottom: 3px solid #e8eaf6;
                }
                .kpi-summary {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
                    gap: 10px;
                    margin-bottom: 15px;
                }
                .kpi-summary .kpi-box {
                    background: white;
                    border-radius: 10px;
                    padding: 12px 15px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.06);
                    border: 1px solid #e8eaf6;
                }
                .kpi-summary .kpi-box .kpi-value {
                    font-size: 24px;
                    font-weight: 700;
                    color: #1a237e;
                }
                .kpi-summary .kpi-box .kpi-label {
                    font-size: 11px;
                    color: #6c757d;
                    margin-top: 2px;
                }
                .kpi-summary .kpi-box.critical .kpi-value { color: #dc3545; }
                .kpi-summary .kpi-box.high .kpi-value { color: #fd7e14; }
                .kpi-summary .kpi-box.medium .kpi-value { color: #ffc107; }
                .kpi-summary .kpi-box.low .kpi-value { color: #28a745; }
                .kpi-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                    margin-bottom: 15px;
                }
                .kpi-card {
                    background: white;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.06);
                    border: 1px solid #e8eaf6;
                }
                .kpi-card h3 {
                    font-size: 13px;
                    font-weight: 600;
                    color: #1a237e;
                    margin-bottom: 10px;
                    padding-bottom: 6px;
                    border-bottom: 2px solid #e8eaf6;
                }
                .kpi-card .legend {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-top: 8px;
                    padding-top: 8px;
                    border-top: 1px solid #eee;
                }
                .kpi-card .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    font-size: 10px;
                    color: #495057;
                }
                .kpi-card .legend-item .color-box {
                    width: 14px;
                    height: 14px;
                    border-radius: 3px;
                    border: 1px solid #dee2e6;
                }
                .bar-chart {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                .bar-row {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .bar-row .bar-label {
                    width: 60px;
                    font-size: 11px;
                    color: #495057;
                    text-align: right;
                }
                .bar-row .bar-track {
                    flex: 1;
                    height: 16px;
                    background: #f0f0f0;
                    border-radius: 8px;
                    overflow: hidden;
                }
                .bar-row .bar-fill {
                    height: 100%;
                    border-radius: 8px;
                }
                .bar-row .bar-value {
                    width: 30px;
                    font-size: 11px;
                    font-weight: 600;
                    color: #1a237e;
                }
                /* Heatmaps with tooltip */
                .heatmaps-row {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                }
                .heatmap-wrapper {
                    background: white;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.06);
                    border: 1px solid #e8eaf6;
                }
                .heatmap-wrapper h3 {
                    font-size: 13px;
                    font-weight: 600;
                    color: #1a237e;
                    margin-bottom: 10px;
                    padding-bottom: 6px;
                    border-bottom: 2px solid #e8eaf6;
                }
                .heatmap-table {
                    width: 100%;
                    max-width: 350px;
                    margin: 0 auto;
                    border-collapse: collapse;
                }
                .heatmap-table th, .heatmap-table td {
                    border: 1px solid #dee2e6;
                    padding: 8px;
                    text-align: center;
                    min-width: 30px;
                    font-size: 12px;
                }
                .heatmap-table .label-cell {
                    background: #f8f9fa;
                    font-weight: 600;
                    color: #495057;
                    min-width: 50px;
                    font-size: 10px;
                }
                .heatmap-table .header-cell {
                    background: #f8f9fa;
                    font-weight: 600;
                    color: #495057;
                    font-size: 10px;
                }
                .heatmap-table .cell {
                    font-weight: 600;
                    transition: all 0.2s ease;
                    position: relative;
                    cursor: default;
                    min-height: 30px;
                    vertical-align: middle;
                }
                .heatmap-table .cell.has-risks {
                    cursor: pointer;
                    border: 2px solid rgba(255,255,255,0.5);
                }
                .heatmap-table .cell.has-risks:hover {
                    transform: scale(1.08);
                    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
                    z-index: 10;
                }
                .heatmap-table .cell .risk-count {
                    font-size: 14px;
                    font-weight: 700;
                    color: white;
                    text-shadow: 0 1px 4px rgba(0,0,0,0.3);
                }
                .heatmap-table .cell .tooltip-text {
                    display: none;
                    position: absolute;
                    background: #1a237e;
                    color: white;
                    padding: 6px 10px;
                    border-radius: 6px;
                    font-size: 10px;
                    z-index: 999;
                    bottom: 110%;
                    left: 50%;
                    transform: translateX(-50%);
                    min-width: 150px;
                    max-width: 250px;
                    white-space: normal;
                    text-align: left;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                    line-height: 1.4;
                }
                .heatmap-table .cell .tooltip-text:after {
                    content: '';
                    position: absolute;
                    bottom: -6px;
                    left: 50%;
                    transform: translateX(-50%);
                    border-left: 6px solid transparent;
                    border-right: 6px solid transparent;
                    border-top: 6px solid #1a237e;
                }
                .heatmap-table .cell .tooltip-text .risk-item {
                    padding: 2px 0;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }
                .heatmap-table .cell .tooltip-text .risk-item:last-child {
                    border-bottom: none;
                }
                .heatmap-table .cell .tooltip-text .risk-code {
                    font-weight: 700;
                    color: #ffc107;
                }
                .heatmap-table .cell .tooltip-text .risk-level {
                    font-size: 8px;
                    padding: 1px 6px;
                    border-radius: 10px;
                    margin-left: 4px;
                }
                .heatmap-table .cell .tooltip-text .risk-level.critical { background: #dc3545; }
                .heatmap-table .cell .tooltip-text .risk-level.high { background: #fd7e14; }
                .heatmap-table .cell .tooltip-text .risk-level.medium { background: #ffc107; color: #000; }
                .heatmap-table .cell .tooltip-text .risk-level.low { background: #28a745; }
                .heatmap-table .cell.has-risks:hover .tooltip-text {
                    display: block;
                }
                .heatmap-table .cell.empty {
                    opacity: 0.15;
                    cursor: default !important;
                }
                .heatmap-table .cell.empty:hover {
                    transform: none !important;
                    box-shadow: none !important;
                }
                .heatmap-legend {
                    display: flex;
                    justify-content: center;
                    gap: 10px;
                    margin-top: 10px;
                    flex-wrap: wrap;
                    padding: 8px 12px;
                    background: #f8f9fa;
                    border-radius: 6px;
                }
                .heatmap-legend .legend-item {
                    display: flex;
                    align-items: center;
                    gap: 4px;
                    font-size: 10px;
                    color: #495057;
                }
                .heatmap-legend .color-box {
                    width: 16px;
                    height: 16px;
                    border-radius: 3px;
                    border: 1px solid #dee2e6;
                }
                .heatmap-total {
                    text-align: center;
                    margin-top: 8px;
                    font-size: 11px;
                    color: #6c757d;
                }
                @media (max-width: 768px) {
                    .kpi-grid, .heatmaps-row {
                        grid-template-columns: 1fr;
                    }
                }
            </style>

            <div class="kpi-dashboard">
                <h2>🎯 Risk Management KPI Dashboard</h2>

                <!-- KPI Summary -->
                <div class="kpi-summary">
                    <div class="kpi-box">
                        <div class="kpi-value">""" + str(total_risks) + """</div>
                        <div class="kpi-label">Total Risques</div>
                    </div>
                    <div class="kpi-box critical">
                        <div class="kpi-value">""" + str(critical) + """</div>
                        <div class="kpi-label">🔴 Critiques</div>
                    </div>
                    <div class="kpi-box high">
                        <div class="kpi-value">""" + str(high) + """</div>
                        <div class="kpi-label">🟠 Élevés</div>
                    </div>
                    <div class="kpi-box medium">
                        <div class="kpi-value">""" + str(medium) + """</div>
                        <div class="kpi-label">🟡 Moyens</div>
                    </div>
                    <div class="kpi-box low">
                        <div class="kpi-value">""" + str(low) + """</div>
                        <div class="kpi-label">🟢 Faibles</div>
                    </div>
                    <div class="kpi-box">
                        <div class="kpi-value">""" + str(avg_score) + """</div>
                        <div class="kpi-label">📊 Score moyen</div>
                    </div>
                </div>

                <!-- Grid 2 colonnes -->
                <div class="kpi-grid">
                    <!-- Inherent Risk By Period -->
                    <div class="kpi-card">
                        <h3>📈 Inherent Risk By Period</h3>
                        <div class="bar-chart">
            """

        periods = [
            {'name': 'Critiques', 'value': critical, 'color': '#dc3545'},
            {'name': 'Élevés', 'value': high, 'color': '#fd7e14'},
            {'name': 'Moyens', 'value': medium, 'color': '#ffc107'},
            {'name': 'Faibles', 'value': low, 'color': '#28a745'},
        ]
        max_period = max([p['value'] for p in periods]) or 1

        for period in periods:
            pct = round((period['value'] / max_period) * 100, 1) if max_period > 0 else 0
            html += f"""
                            <div class="bar-row">
                                <span class="bar-label">{period['name']}</span>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width:{pct}%;background:{period['color']};"></div>
                                </div>
                                <span class="bar-value">{period['value']}</span>
                            </div>
                """

        html += """
                        </div>
                        <div class="legend">
                            <span class="legend-item"><span class="color-box" style="background:#dc3545;"></span> Critical</span>
                            <span class="legend-item"><span class="color-box" style="background:#fd7e14;"></span> High</span>
                            <span class="legend-item"><span class="color-box" style="background:#ffc107;"></span> Medium</span>
                            <span class="legend-item"><span class="color-box" style="background:#28a745;"></span> Low</span>
                        </div>
                    </div>

                    <!-- Risk Category By Total Risk Rating -->
                    <div class="kpi-card">
                        <h3>📊 Risk Category By Total Risk Rating</h3>
                        <div class="bar-chart">
            """

        category_colors = ['#1a237e', '#0d47a1', '#1565c0', '#1e88e5', '#42a5f5', '#90caf9']
        max_cat = max([v['count'] for v in category_stats.values()]) or 1
        cat_idx = 0
        for cat_name, cat_data in category_stats.items():
            pct = round((cat_data['count'] / max_cat) * 100, 1) if max_cat > 0 else 0
            color = category_colors[cat_idx % len(category_colors)]
            html += f"""
                            <div class="bar-row">
                                <span class="bar-label">{cat_name[:12]}</span>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width:{pct}%;background:{color};"></div>
                                </div>
                                <span class="bar-value">{cat_data['count']}</span>
                            </div>
                """
            cat_idx += 1

        html += """
                        </div>
                    </div>

                    <!-- Residual Risk By Period -->
                    <div class="kpi-card">
                        <h3>📉 Residual Risk By Period</h3>
                        <div class="bar-chart">
            """

        residual_periods = [
            {'name': 'Critiques', 'value': len([r for r in risks if r.residual_level == 'critical']),
             'color': '#dc3545'},
            {'name': 'Élevés', 'value': len([r for r in risks if r.residual_level == 'high']), 'color': '#fd7e14'},
            {'name': 'Moyens', 'value': len([r for r in risks if r.residual_level == 'medium']), 'color': '#ffc107'},
            {'name': 'Faibles', 'value': len([r for r in risks if r.residual_level == 'low']), 'color': '#28a745'},
        ]
        max_residual = max([p['value'] for p in residual_periods]) or 1

        for period in residual_periods:
            pct = round((period['value'] / max_residual) * 100, 1) if max_residual > 0 else 0
            html += f"""
                            <div class="bar-row">
                                <span class="bar-label">{period['name']}</span>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width:{pct}%;background:{period['color']};"></div>
                                </div>
                                <span class="bar-value">{period['value']}</span>
                            </div>
                """

        html += """
                        </div>
                        <div class="legend">
                            <span class="legend-item"><span class="color-box" style="background:#dc3545;"></span> Critical</span>
                            <span class="legend-item"><span class="color-box" style="background:#fd7e14;"></span> High</span>
                            <span class="legend-item"><span class="color-box" style="background:#ffc107;"></span> Medium</span>
                            <span class="legend-item"><span class="color-box" style="background:#28a745;"></span> Low</span>
                        </div>
                    </div>

                    <!-- Control Rate By Period -->
                    <div class="kpi-card">
                        <h3>🎯 Control Rate By Period</h3>
                        <div class="bar-chart">
            """

        control_periods = [
            {'name': 'Efficaces', 'value': control_stats['effective'], 'color': '#28a745'},
            {'name': 'Partiels', 'value': control_stats['partial'], 'color': '#ffc107'},
            {'name': 'Inefficaces', 'value': control_stats['ineffective'], 'color': '#dc3545'},
        ]
        max_control = max([p['value'] for p in control_periods]) or 1

        for period in control_periods:
            pct = round((period['value'] / max_control) * 100, 1) if max_control > 0 else 0
            html += f"""
                            <div class="bar-row">
                                <span class="bar-label">{period['name'][:8]}</span>
                                <div class="bar-track">
                                    <div class="bar-fill" style="width:{pct}%;background:{period['color']};"></div>
                                </div>
                                <span class="bar-value">{period['value']}</span>
                            </div>
                """

        html += """
                        </div>
                        <div class="legend">
                            <span class="legend-item"><span class="color-box" style="background:#28a745;"></span> Effective</span>
                            <span class="legend-item"><span class="color-box" style="background:#ffc107;"></span> Partially Effective</span>
                            <span class="legend-item"><span class="color-box" style="background:#dc3545;"></span> Ineffective</span>
                        </div>
                    </div>
                </div>

                <!-- Heatmaps side by side -->
                <div class="heatmaps-row">
                    <!-- Heatmap avec survole -->
                    <div class="heatmap-wrapper">
                        <h3>🔥 Heat Map (survolez pour les détails)</h3>
                        <table class="heatmap-table">
                            <tr>
                                <th class="label-cell">Gravité →</th>
            """

        for i in range(1, 6):
            html += f'<th class="header-cell">{i}</th>'
        html += '</tr>'

        for prob in range(5, 0, -1):
            html += f'<tr><td class="label-cell">{prob}</td>'
            for impact in range(1, 6):
                score = prob * impact
                color = self._get_heatmap_color(score)
                key = f"{prob}_{impact}"
                risks_in_cell = matrix_data.get(key, [])

                if risks_in_cell:
                    tooltip_lines = []
                    for r in risks_in_cell[:5]:  # Limiter à 5 risques pour le tooltip
                        level_class = r['level'] or 'unknown'
                        tooltip_lines.append(
                            f'<div class="risk-item"><span class="risk-code">{r["code"]}</span> - {r["name"]} '
                            f'<span class="risk-level {level_class}">{r["level"] or "N/A"}</span>'
                            f' <span style="font-size:8px;color:#aaa;">score: {r["score"]}</span></div>'
                        )
                    if len(risks_in_cell) > 5:
                        tooltip_lines.append(f'<div class="risk-item">... et {len(risks_in_cell) - 5} autres</div>')
                    tooltip_text = ''.join(tooltip_lines)
                    count = len(risks_in_cell)
                    html += f'''
                        <td class="cell has-risks" style="background-color:{color};color:white;">
                            <span class="risk-count">{count}</span>
                            <div class="tooltip-text">{tooltip_text}</div>
                        </td>
                        '''
                else:
                    html += f'<td class="cell empty" style="background-color:{color};color:white;opacity:0.15;">&nbsp;</td>'
            html += '</tr>'

        html += """
                        </table>
                        <div class="heatmap-legend">
                            <span class="legend-item">
                                <span class="color-box" style="background:#28a745;"></span> Faible
                            </span>
                            <span class="legend-item">
                                <span class="color-box" style="background:#ffc107;"></span> Moyen
                            </span>
                            <span class="legend-item">
                                <span class="color-box" style="background:#fd7e14;"></span> Élevé
                            </span>
                            <span class="legend-item">
                                <span class="color-box" style="background:#dc3545;"></span> Critique
                            </span>
                        </div>
                        <div class="heatmap-total">Total: """ + str(total_risks) + """ risques</div>
                    </div>

                    <!-- Residual Risk Heat Map -->
                    <div class="heatmap-wrapper">
                        <h3>🔥 Residual Risk Heat Map</h3>
                        <table class="heatmap-table">
                            <tr>
                                <th class="label-cell">Gravité →</th>
            """

        labels = ['Insig', 'Minor', 'Mod', 'Major', 'Catas']
        for label in labels:
            html += f'<th class="header-cell">{label}</th>'
        html += '</tr>'

        prob_labels = ['Remote', 'Unlikely', 'Possible', 'H.Prob', 'Certain']
        for prob_idx, prob_label in enumerate(prob_labels):
            html += f'<tr><td class="label-cell">{prob_label}</td>'
            prob = prob_idx + 1
            for impact in range(1, 6):
                score = prob * impact
                color = self._get_heatmap_color(score)
                key = f"{prob}_{impact}"
                cell_data = residual_matrix.get(key, 0)
                if cell_data > 0:
                    html += f'<td class="cell has-risks" style="background-color:{color};color:white;cursor:pointer;" title="{cell_data} risque(s) résiduel(s)">'
                    html += f'<span class="risk-count">{cell_data}</span>'
                    html += '</td>'
                else:
                    html += f'<td class="cell empty" style="background-color:{color};color:white;opacity:0.15;">&nbsp;</td>'
            html += '</tr>'

        html += """
                        </table>
                        <div class="heatmap-legend">
                            <span class="legend-item">
                                <span class="color-box" style="background:#28a745;"></span> Faible
                            </span>
                            <span class="legend-item">
                                <span class="color-box" style="background:#ffc107;"></span> Moyen
                            </span>
                            <span class="legend-item">
                                <span class="color-box" style="background:#fd7e14;"></span> Élevé
                            </span>
                            <span class="legend-item">
                                <span class="color-box" style="background:#dc3545;"></span> Critique
                            </span>
                        </div>
                        <div class="heatmap-total">Résiduels: """ + str(
            len([r for r in risks if r.residual_level in ['critical', 'high', 'medium', 'low']])) + """ risques</div>
                    </div>
                </div>
            </div>
            """

        for record in self:
            record.dashboard_html = html

    def get_executive_dashboard_data(self):
        """Retourne les données pour le tableau de bord exécutif"""

        risks = self.search([('active', '=', True)])
        total_risks = len(risks)

        # Statistiques par niveau
        critical = len([r for r in risks if r.inherent_level == 'critical'])
        high = len([r for r in risks if r.inherent_level == 'high'])
        medium = len([r for r in risks if r.inherent_level == 'medium'])
        low = len([r for r in risks if r.inherent_level == 'low'])

        # Score moyen
        total_score = sum([r.inherent_score or 0 for r in risks])
        avg_score = round(total_score / total_risks, 1) if total_risks > 0 else 0

        # Risques hors appétit
        over_appetite = []
        for r in risks:
            if r.inherent_level in ['critical', 'high'] and (r.inherent_score or 0) >= 15:
                over_appetite.append({
                    'id': r.id,
                    'name': r.name,
                    'code': r.code,
                    'level': r.inherent_level,
                    'score': r.inherent_score,
                    'state': r.state,
                })
        over_appetite = sorted(over_appetite, key=lambda x: x['score'], reverse=True)[:5]

        # Top 5 risques
        top_risks = []
        for r in risks.sorted(key=lambda x: x.inherent_score or 0, reverse=True)[:5]:
            top_risks.append({
                'id': r.id,
                'name': r.name,
                'code': r.code,
                'level': r.inherent_level,
                'score': r.inherent_score,
                'state': r.state,
            })

        # Matrice 5x5
        matrix_data = {}
        for i in range(1, 6):
            for j in range(1, 6):
                matrix_data[f"{i}_{j}"] = []

        for risk in risks:
            impact = int(risk.inherent_impact or 1)
            prob = int(risk.inherent_probability or 1)
            key = f"{prob}_{impact}"
            if key in matrix_data:
                matrix_data[key].append({
                    'id': risk.id,
                    'name': risk.name,
                    'code': risk.code,
                    'level': risk.inherent_level,
                    'score': risk.inherent_score,
                })

        # Catégories
        category_stats = {}
        for risk in risks:
            cat = risk.category_id.name or 'Non catégorisé'
            if cat not in category_stats:
                category_stats[cat] = 0
            category_stats[cat] += 1

        # Statistiques des actions
        action_stats = {
            'not_started': len([r for r in risks if r.state == 'draft']),
            'in_progress': len([r for r in risks if r.state == 'validated']),
            'completed': len([r for r in risks if r.state == 'obsolete']),
            'delayed': 0,
        }

        # Tous les risques
        all_risks = []
        for r in risks:
            all_risks.append({
                'id': r.id,
                'name': r.name,
                'code': r.code,
                'level': r.inherent_level,
                'score': r.inherent_score,
                'state': r.state,
            })

        # Narratives
        narratives = [
            {'icon': '🔺', 'text': 'Nouveau risque identifié : Risque de réputation'},
            {'icon': '📈', 'text': 'Augmentation du risque Cyber (passage de 16 à 20)'},
            {'icon': '✅', 'text': 'Mise en place du plan de continuité pour le fournisseur clé'},
        ]

        return {
            'total_risks': total_risks,
            'critical': critical,
            'high': high,
            'medium': medium,
            'low': low,
            'avg_score': avg_score,
            'posture_status': '✅ Dans appétit' if critical <= 2 else '⚠️ À surveiller' if critical <= 4 else '🔴 Hors appétit',
            'over_appetite': over_appetite,
            'top_risks': top_risks,
            'matrix_data': matrix_data,
            'category_stats': category_stats,
            'action_stats': action_stats,
            'narratives': narratives,
            'all_risks': all_risks,
        }

    document_ids = fields.Many2many(
        'risk.document',
        string='Documents de gouvernance',
        help="Documents de gouvernance liés à ce risque"
    )

    document_count = fields.Integer(
        compute='_compute_document_count',
        store=True,
        string="Nombre de documents"
    )

    @api.depends('document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)

    def action_view_documents(self):
        """Ouvre la liste des documents liés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Documents - {self.name}',
            'res_model': 'risk.document',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', self.document_ids.ids)],
            'context': {'default_risk_ids': [(4, self.id)]},
        }

    def action_view_action_plans(self):
        """Voir tous les plans d'action associés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Plans d\'action - {self.name}',
            'res_model': 'risk.action.plan',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', self.action_plan_ids.ids)],
        }