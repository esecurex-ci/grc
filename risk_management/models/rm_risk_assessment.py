from odoo import models, fields, api


class RiskAssessment(models.Model):
    _name = 'risk.assessment'
    _description = 'Evaluation des risques'
    _order = 'assessment_date'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'assessment_date desc'

    name = fields.Char(
        readonly=True,
        default='New',
        string='Nom',
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
        tracking=True
    )

    assessor_id = fields.Many2one(
        'hr.employee',
        string='Assessor'
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company
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
        store=True
    )

    ##################################################################
    # RISQUE RESIDUEL
    ##################################################################

    residual_probability = fields.Integer(default=1, compute='_compute_residual_probability')

    residual_impact = fields.Integer(
        default=1
    )

    residual_score = fields.Integer(
        compute='_compute_scores',
        store=True,
        string='Score Résiduel',
    )

    ##################################################################
    # NIVEAU DE RISQUE
    ##################################################################

    risk_level = fields.Selection(
        [
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('important', 'Important'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        compute='_compute_risk_level',
        store=True
    )

    ##################################################################
    # APPETENCE
    ##################################################################

    appetite = fields.Selection(
        related='risk_id.appetite',
        store=True
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
            ('accept', 'Accept'),
            ('mitigate', 'Mitigate'),
            ('transfer', 'Transfer'),
            ('avoid', 'Avoid')
        ]
    )

    comment = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Soummis'),
            ('reviewed', 'Révu'),
            ('approved', 'Aprrouvé'),
            ('closed', 'Archivé')
        ],
        default='draft',
        tracking=True
    )

    treatment_plan_ids = fields.One2many(
        'risk.treatment.plan',
        'assessment_id'
    )

    treatment_plan_count = fields.Integer(
        compute='_compute_treatment_plan_count'
    )

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

    @api.depends(
        'inherent_probability',
        'control_effectiveness'
    )
    def _compute_residual_probability(self):

        for rec in self:
            reduction = (
                    rec.control_effectiveness / 100
            )

            rec.residual_probability = max(
                1,
                round(
                    rec.inherent_probability
                    *
                    (1 - reduction)
                )
            )

    @api.depends(
        'inherent_probability',
        'inherent_impact',
        'residual_probability',
        'residual_impact'
    )
    def _compute_scores(self):
        for rec in self:

            rec.inherent_score = (
                rec.inherent_probability *
                rec.inherent_impact
            )

            rec.residual_score = (
                rec.residual_probability *
                rec.residual_impact
            )

    @api.depends('residual_score')
    def _compute_risk_level(self):

        for rec in self:

            if rec.residual_score >= 20:
                rec.risk_level = 'critical'

            elif rec.residual_score >= 15:
                rec.risk_level = 'high'

            elif rec.residual_score >= 10:
                rec.risk_level = 'important'

            elif rec.residual_score >= 5:
                rec.risk_level = 'moderate'

            else:
                rec.risk_level = 'low'

    @api.depends('risk_level', 'appetite')
    def _compute_over_appetite(self):

        ranking = {
            'very_low': 1,
            'low': 2,
            'medium': 3,
            'high': 4,
            'critical': 5
        }

        risk_ranking = {
            'low': 1,
            'moderate': 2,
            'important': 3,
            'high': 4,
            'critical': 5
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
        self.write({'state': 'approved'})

    def action_close(self):
        self.write({'state': 'closed'})

    def action_reset(self):
        self.write({'state': 'draft'})