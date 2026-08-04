from odoo import models, fields, api


class RiskAssessment(models.Model):
    _name = 'risk.assessment'
    _description = 'Evaluation des risques'
    _order = 'assessment_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

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

    inherent_probability = fields.Selection(
        selection='_get_probability_selection',
        string='Probabilité Inhérente',
        default='3'
    )

    inherent_impact = fields.Selection(
        selection='_get_impact_selection',
        string='Impact Inhérent',
        default='3'
    )

    inherent_score = fields.Integer(
        compute='_compute_scores',
        store=True,
        string='Score Inhérent',
    )

    def _get_probability_selection(self):
        """Réutilise directement la même échelle que risk.risk — une seule source de vérité."""
        return self.env['risk.risk']._get_probability_selection()

    def _get_impact_selection(self):
        """Réutilise directement la même échelle que risk.risk — une seule source de vérité."""
        return self.env['risk.risk']._get_impact_selection()

    ##################################################################
    # CONTROLES
    # ⚠️ Ce niveau est choisi manuellement par l'évaluateur (pré-rempli
    # par défaut avec le niveau actuel du risque), et non plus calculé
    # automatiquement — cohérent avec le fait que risk.control.effectiveness
    # est traité de façon incohérente selon les endroits du système
    # (réserve documentée dans le cahier des charges, EXG-KRI-13).
    ##################################################################

    control_ids_preview = fields.Many2many(
        'risk.control',
        related='risk_id.control_ids',
        string='Contrôles du risque',
        help="Affiché pour référence uniquement : les contrôles déjà enregistrés "
             "pour ce risque, afin que l'évaluateur les voie avant de juger de "
             "leur efficacité. Ne modifie rien ici — pour ajouter/modifier un "
             "contrôle, passe par la fiche du risque lui-même."
    )

    control_effectiveness_level = fields.Selection(
        [
            ('ineffective', 'Inefficace ou informel'),
            ('partially_effective', 'Partiellement efficace'),
            ('effective', 'Efficace'),
        ],
        string="Niveau d'efficacité des contrôles",
        tracking=True,
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
        """Pré-remplit la probabilité/impact inhérents et le niveau d'efficacité des
        contrôles avec les valeurs actuelles du risque, pour éviter à l'évaluateur de
        tout ressaisir de mémoire. Il peut ensuite ajuster chaque valeur s'il estime
        que la situation a évolué depuis la dernière évaluation."""
        for rec in self:
            if rec.risk_id:
                rec.inherent_probability = rec.risk_id.inherent_probability or '3'
                rec.inherent_impact = rec.risk_id.inherent_impact or '3'
                rec.control_effectiveness_level = rec.risk_id.control_effectiveness_level or 'ineffective'

    @api.depends('inherent_probability', 'inherent_impact')
    def _compute_scores(self):
        for rec in self:
            rec.inherent_score = int(rec.inherent_probability or 1) * int(rec.inherent_impact or 1)

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
        met à jour la probabilité/impact inhérents et le niveau d'efficacité des
        contrôles du risque.

        Ceci suppose que risk.risk.control_effectiveness_level n'est plus un champ
        recalculé en continu, mais un champ simple (suggéré automatiquement depuis les
        contrôles liés, modifiable manuellement) — l'approbation peut donc l'écraser
        directement, exactement comme pour la probabilité/impact inhérents.
        """
        self.write({'state': 'approved'})
        for rec in self:
            if rec.risk_id:
                rec.risk_id.write({
                    'inherent_probability': rec.inherent_probability,
                    'inherent_impact': rec.inherent_impact,
                    'control_effectiveness_level': rec.control_effectiveness_level,
                })

    def action_close(self):
        self.write({'state': 'closed'})

    def action_reset(self):
        self.write({'state': 'draft'})