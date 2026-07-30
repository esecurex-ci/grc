from odoo import models, fields, api


class RiskAssessment(models.Model):
    _name = 'risk.assessment'
    _description = 'Evaluation des risques'
    _order = 'assessment_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Seuils de conversion de l'efficacité moyenne des contrôles (%) vers un niveau qualitatif.
    # ⚠️ Valeurs par défaut proposées, à valider/ajuster selon ton contexte métier
    # (idéalement à terme configurables via un écran de paramétrage, comme l'échelle de risque).
    CONTROL_EFFECTIVENESS_INEFFECTIVE_MAX = 40
    CONTROL_EFFECTIVENESS_PARTIAL_MAX = 70

    _sql_constraints = [
        (
            'unique_risk_period',
            'unique(risk_id, period_id)',
            "Une évaluation existe déjà pour ce risque sur cette période."
        ),
    ]

    name = fields.Char(
        readonly=True,
        default='New',
        string='Désignation',
    )

    assessment_date = fields.Date(
        default=fields.Date.today,
        required=True,
        string='Date Clôture'
    )

    risk_id = fields.Many2one(
        'risk.risk',
        required=True,
        ondelete='cascade',
        tracking=True,
        string='Risque'
    )

    period_id = fields.Many2one(
        'risk.assessment.period',
        required=True,
        tracking=True,
        string='Période'
    )

    assessor_id = fields.Many2one(
        'hr.employee',
        string='Responsable'
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        string='Société'
    )

    ##################################################################
    # RISQUE BRUT
    ##################################################################

    inherent_probability = fields.Integer(
        string=' Probabilité Inhérente',
        default=1
    )

    inherent_impact = fields.Integer(
        string='Impact Inhérent ',
        default=1
    )

    inherent_score = fields.Integer(
        compute='_compute_scores',
        store=True,
        string='Score Inhérent',
    )

    ##################################################################
    # CONTROLES
    ##################################################################

    control_effectiveness = fields.Float(
        compute='_compute_control_effectiveness',
        store=True,
        string='Effectivité des Contrôles',
    )

    ##################################################################
    # RISQUE RESIDUEL
    # ⚠️ Pas de score numérique pour le résiduel (conforme à l'échelle
    # métier réelle) : le niveau résiduel est déterminé qualitativement
    # par la même matrice que risk.risk (niveau inhérent + efficacité
    # des contrôles), pas par un calcul probabilité × impact.
    ##################################################################

    inherent_level = fields.Selection(
        [
            ('low', 'Faible'),
            ('medium', 'Modéré'),
            ('high', 'Élevé'),
        ],
        compute='_compute_inherent_level',
        store=True,
        string='Niveau Inhérent',
    )

    control_effectiveness_level = fields.Selection(
        [
            ('ineffective', 'Inefficace'),
            ('partially_effective', 'Partiellement efficace'),
            ('effective', 'Efficace'),
        ],
        compute='_compute_control_effectiveness_level',
        store=True,
        string='Niveau d\'efficacité des contrôles',
    )

    ##################################################################
    # NIVEAU DE RISQUE (niveau résiduel net, échelle réelle à 3 niveaux)
    ##################################################################

    risk_level = fields.Selection(
        [
            ('low', 'Faible'),
            ('medium', 'Modéré'),
            ('high', 'Élevé'),
        ],
        compute='_compute_risk_level',
        store=True,
        string='Niveau de risque résiduel',
    )

    ##################################################################
    # APPETENCE
    ##################################################################

    appetite = fields.Selection(
        related='risk_id.appetite',
        store=True,
        string='Risque Appetit'
    )

    over_appetite = fields.Boolean(
        compute='_compute_over_appetite',
        store=True
    )

    ##################################################################
    # TRAITEMENT
    ##################################################################

    treatment_strategy = fields.Selection(
        [
            ('accept', 'Accepter'),
            ('mitigate', 'Atténuer'),
            ('transfer', 'Transférer'),
            ('avoid', 'Éviter')
        ],
        string='Stratégie de traitement'
    )

    comment = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('submitted', 'Soumis'),
            ('reviewed', 'Révisé'),
            ('approved', 'Approuvé'),
            ('closed', 'Archivé')
        ],
        default='draft',
        tracking=True,
        string='Statut'
    )

    treatment_plan_ids = fields.One2many(
        'risk.treatment.plan',
        'assessment_id'
    )

    action_plan_ids = fields.Many2many(
        'risk.action.plan',
        string='Plans d\'action associés',
        help="Plans d'action liés à ce traitement"
    )

    treatment_plan_count = fields.Integer(
        compute='_compute_treatment_plan_count'
    )

    @api.onchange('risk_id')
    def _onchange_risk_id(self):
        """Pré-remplit la probabilité/impact inhérents avec les valeurs actuelles du risque,
        pour éviter à l'évaluateur de tout ressaisir de mémoire. Il peut ensuite ajuster
        s'il estime que le risque a évolué depuis la dernière évaluation.

        ⚠️ risk.risk stocke ces champs en Selection (texte '1'-'5'), alors qu'ici ce sont
        des Integer : conversion explicite nécessaire.
        """
        for rec in self:
            if rec.risk_id:
                try:
                    rec.inherent_probability = int(rec.risk_id.inherent_probability or 1)
                except (ValueError, TypeError):
                    rec.inherent_probability = 1
                try:
                    rec.inherent_impact = int(rec.risk_id.inherent_impact or 1)
                except (ValueError, TypeError):
                    rec.inherent_impact = 1

    @api.depends('risk_id.control_ids.effectiveness')
    def _compute_control_effectiveness(self):

        for rec in self:

            controls = rec.risk_id.control_ids

            if controls:

                rec.control_effectiveness = (
                        sum(
                            controls.mapped(
                                'effectiveness'
                            )
                        )
                        /
                        len(controls)
                )

            else:
                rec.control_effectiveness = 0

    @api.depends('inherent_probability', 'inherent_impact')
    def _compute_scores(self):
        for rec in self:
            rec.inherent_score = rec.inherent_probability * rec.inherent_impact

    @api.depends('inherent_score')
    def _compute_inherent_level(self):
        """Réutilise la même échelle réelle que risk.risk (Faible 1-5 / Modéré 6-15 / Élevé 16-25)"""
        for rec in self:
            score = rec.inherent_score or 0
            if score <= 5:
                rec.inherent_level = 'low'
            elif score <= 15:
                rec.inherent_level = 'medium'
            else:
                rec.inherent_level = 'high'

    @api.depends('control_effectiveness')
    def _compute_control_effectiveness_level(self):
        """Convertit l'efficacité moyenne des contrôles (%) en niveau qualitatif à 3 valeurs"""
        for rec in self:
            effectiveness = rec.control_effectiveness or 0
            if effectiveness < self.CONTROL_EFFECTIVENESS_INEFFECTIVE_MAX:
                rec.control_effectiveness_level = 'ineffective'
            elif effectiveness < self.CONTROL_EFFECTIVENESS_PARTIAL_MAX:
                rec.control_effectiveness_level = 'partially_effective'
            else:
                rec.control_effectiveness_level = 'effective'

    @api.depends('inherent_level', 'control_effectiveness_level')
    def _compute_risk_level(self):
        """
        Détermine le niveau de risque résiduel (net) en réutilisant directement
        la même matrice qualitative que risk.risk (_get_residual_level_from_matrix),
        sans dupliquer la logique ni calculer de score numérique.
        """
        for rec in self:
            if rec.risk_id and rec.inherent_level:
                rec.risk_level = rec.risk_id._get_residual_level_from_matrix(
                    rec.inherent_level,
                    rec.control_effectiveness_level or 'ineffective'
                )
            else:
                rec.risk_level = 'low'

    @api.depends('risk_level', 'appetite')
    def _compute_over_appetite(self):

        # Échelle d'appétit propre à risk.risk (5 valeurs réelles, non touchée)
        ranking = {
            'very_low': 1,
            'low': 2,
            'medium': 3,
            'high': 4,
            'critical': 5
        }

        # Le niveau de risque résiduel n'a que 3 paliers réels (Faible/Modéré/Élevé),
        # contre 5 pour l'appétit. On les étale proportionnellement sur la même
        # échelle 1-5 (1/3/5) plutôt que de comparer des rangs 1-3 à des rangs 1-5,
        # ce qui fausserait la comparaison (un risque "Élevé" ne dépasserait jamais
        # un appétit "Moyen" ou plus, ce qui n'a pas de sens).
        risk_ranking = {
            'low': 1,
            'medium': 3,
            'high': 5,
        }

        for rec in self:

            appetite = ranking.get(
                rec.appetite,
                3
            )

            risk = risk_ranking.get(
                rec.risk_level,
                1
            )

            rec.over_appetite = risk > appetite

    @api.depends('treatment_plan_ids')
    def _compute_treatment_plan_count(self):

        for rec in self:
            rec.treatment_plan_count = len(
                rec.treatment_plan_ids
            )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('name', 'New') == 'New':

                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'risk.assessment'
                )

        return super().create(vals_list)

    ##################################################################
    # WORKFLOW
    ##################################################################

    def action_submit(self):
        self.write({'state': 'submitted'})

    def action_review(self):
        self.write({'state': 'reviewed'})

    def action_approve(self):
        """
        Approuve l'évaluation et répercute ses résultats sur la fiche risque officielle
        (risk.risk). C'est le point d'entrée qui fait autorité : tant qu'une évaluation
        n'est pas approuvée, elle n'affecte jamais le registre des risques ni les
        tableaux de bord — seule une évaluation validée (donc passée par la gouvernance)
        met à jour la probabilité/impact inhérents du risque.

        Note : control_effectiveness_level n'est pas répercuté ici, car il est déjà
        calculé automatiquement sur risk.risk à partir des mêmes control_ids — les deux
        modèles restent donc cohérents sans synchronisation manuelle nécessaire.
        """
        self.write({'state': 'approved'})
        for rec in self:
            if rec.risk_id:
                rec.risk_id.write({
                    'inherent_probability': str(rec.inherent_probability),
                    'inherent_impact': str(rec.inherent_impact),
                })

    def action_close(self):
        self.write({'state': 'closed'})

    def action_reset(self):
        self.write({'state': 'draft'})