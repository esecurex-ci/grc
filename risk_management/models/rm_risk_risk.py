from dateutil.relativedelta import relativedelta

from odoo import models, fields, api

class RiskRisk(models.Model):
    _name = 'risk.risk'
    _description = 'Risk'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Risque',required=True,tracking=True)
    code = fields.Char(string='Code', readonly=True,default='New',tracking=True)
    description = fields.Html(string='Description')
    cause_description = fields.Html(string='Cause')
    consequence_description = fields.Html(string='Conséquence')
    category_id = fields.Many2one('risk.category', required=True,tracking=True)
    subcategory_id = fields.Many2one('risk.subcategory', tracking=True)
    owner_id = fields.Many2one('hr.employee', string='Risk Owner', tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    appetite = fields.Selection([ ('very_low', 'Very Low'),('low', 'Low'),
        ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical'),], default='medium')
    state = fields.Selection([ ('draft', 'Draft'),('validated', 'Validated'), ('obsolete', 'Obsolete')
    ], default='draft', tracking=True)
    cause_ids = fields.Many2many('risk.cause', string='Causes')
    impact_ids = fields.Many2many('risk.impact', string='Impacts')
    regulation_ids = fields.Many2many(  'risk.regulation',  string='Regulations')
    asset_ids = fields.Many2many('risk.asset', string='Assets')
    organization_ids = fields.Many2many( 'risk.organization',string='Organization Units')
    active = fields.Boolean(default=True)
    control_ids = fields.Many2many('risk.control', string='Controls')
    kri_ids = fields.Many2many('risk.kri', string='KRIs')
    incident_ids = fields.One2many('risk.incident','risk_id')
    incident_count = fields.Integer(compute='_compute_incident_count')
    total_loss_amount = fields.Monetary(compute='_compute_total_loss')
    currency_id = fields.Many2one('res.currency',default=lambda self:self.env.company.currency_id)
    audit_finding_ids = fields.One2many('risk.audit.finding','risk_id')
    audit_finding_count = fields.Integer(compute='_compute_audit_finding_count')
    compliance_requirement_ids = fields.Many2many( 'risk.compliance.requirement',string='Compliance Requirements')
    inherent_probability = fields.Selection([('1', 'Very Low'),('2', 'Low'),('3', 'Medium'), ('4', 'High'),
            ('5', 'Very High')], default='1')
    inherent_impact = fields.Selection([('1', 'Insignificant'),('2', 'Minor'),
            ('3', 'Moderate'),('4', 'Major'),('5', 'Catastrophic')],default='1')
    inherent_score = fields.Integer(compute='_compute_scores',store=True)
    inherent_level = fields.Selection([ ('low', 'Low'),('medium', 'Medium'),
            ('high', 'High'),('critical', 'Critical')],compute='_compute_scores',store=True)
    residual_probability = fields.Selection(
        [
            ('1', 'Very Low'),
            ('2', 'Low'),
            ('3', 'Medium'),
            ('4', 'High'),
            ('5', 'Very High')
        ],
        default='1'
    )
    residual_impact = fields.Selection(
        [
            ('1', 'Insignificant'),
            ('2', 'Minor'),
            ('3', 'Moderate'),
            ('4', 'Major'),
            ('5', 'Catastrophic')
        ],
        default='1'
    )
    residual_score = fields.Integer(
        compute='_compute_scores',
        store=True
    )
    residual_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'),
            ('critical', 'Critical') ],compute='_compute_scores',store=True)
    review_frequency = fields.Selection(
        [('monthly', 'Monthly'),('quarterly', 'Quarterly'),('semiannual', 'Semi-Annual'),('annual', 'Annual')
        ], default='quarterly', tracking=True)

    last_review_date = fields.Date(
        tracking=True
    )

    next_review_date = fields.Date(
        compute='_compute_next_review_date',
        store=True,
        tracking=True
    )

    review_overdue = fields.Boolean(
        compute='_compute_review_overdue',
        store=True
    )
    risk_type = fields.Selection(
        [
            ('strategic', 'Strategic'),
            ('operational', 'Operational'),
            ('financial', 'Financial'),
            ('compliance', 'Compliance'),
            ('cyber', 'Cybersecurity'),
            ('reputation', 'Reputation'),
            ('liquidity', 'Liquidity'),
            ('market', 'Market')
        ],
        string='Risk Type',
        tracking=True
    )
    risk_source = fields.Selection(
        [
            ('internal', 'Internal'),
            ('external', 'External'),
            ('regulatory', 'Regulatory'),
            ('technology', 'Technology'),
            ('human', 'Human'),
            ('supplier', 'Supplier')
        ],
        string='Risk Source',
        tracking=True
    )

    cause = fields.Html(
        string='Cause'
    )

    risk_event = fields.Html(
        string='Risk Event'
    )

    consequence = fields.Html(
        string='Consequence'
    )

    existing_control = fields.Html(
        string='Existing Controls'
    )
    assessment_ids = fields.One2many(
        'risk.assessment',
        'risk_id',
        string='Assessments'
    )

    activity_id = fields.Many2one(
        'risk.activity',
        string='Activité',
        ondelete='set null',
        tracking=True,
        help='Activité concernée par ce risque'
    )

    # Lien vers le processus (via l'activité)
    process_id = fields.Many2one(
        'risk.process',
        related='activity_id.process_id',
        store=True,
        string='Processus'
    )

    risk_level = fields.Selection(
        [
            ('1', 'Très faible'),
            ('2', 'Faible'),
            ('3', 'Moyen'),
            ('4', 'Élevé'),
            ('5', 'Critique')
        ],
        string='Niveau de risque',
        default='1',
        help='Niveau de risque (1 = Très faible, 5 = Critique)'
    )

    # Lien vers le macro-processus (via l'activité)
    macro_process_id = fields.Many2one(
        'risk.macro.process',
        related='activity_id.macro_process_id',
        store=True,
        string='Macro Processus'
    )

    @api.depends(
        'last_review_date',
        'review_frequency'
    )
    def _compute_next_review_date(self):

        for rec in self:

            rec.next_review_date = False

            if not rec.last_review_date:
                continue

            if rec.review_frequency == 'monthly':

                rec.next_review_date = (
                        rec.last_review_date +
                        relativedelta(months=1)
                )

            elif rec.review_frequency == 'quarterly':

                rec.next_review_date = (
                        rec.last_review_date +
                        relativedelta(months=3)
                )

            elif rec.review_frequency == 'semiannual':

                rec.next_review_date = (
                        rec.last_review_date +
                        relativedelta(months=6)
                )

            elif rec.review_frequency == 'annual':

                rec.next_review_date = (
                        rec.last_review_date +
                        relativedelta(years=1)
                )

    @api.depends('next_review_date')
    def _compute_review_overdue(self):

        today = fields.Date.today()

        for rec in self:
            rec.review_overdue = bool(
                rec.next_review_date
                and
                rec.next_review_date < today
            )

    @api.depends(
        'inherent_probability',
        'inherent_impact',
        'residual_probability',
        'residual_impact'
    )
    def _compute_scores(self):

        for rec in self:
            ################################################
            # INHERENT
            ################################################

            inherent = (
                    int(rec.inherent_probability or 1)
                    *
                    int(rec.inherent_impact or 1)
            )

            rec.inherent_score = inherent

            ################################################
            # RESIDUAL
            ################################################

            residual = (
                    int(rec.residual_probability or 1)
                    *
                    int(rec.residual_impact or 1)
            )

            rec.residual_score = residual

            ################################################
            # LEVELS
            ################################################

            rec.inherent_level = \
                rec._get_level(inherent)

            rec.residual_level = \
                rec._get_level(residual)

    def _get_level(self, score):
        if score <= 5:
            return 'low'
        if score <= 10:
            return 'medium'
        if score <= 15:
            return 'high'
        return 'critical'

    @api.depends('audit_finding_ids')
    def _compute_audit_finding_count(self):
        for rec in self:
            rec.audit_finding_count = len(
                rec.audit_finding_ids
            )

    @api.depends('incident_ids')
    def _compute_incident_count(self):

        for rec in self:
            rec.incident_count = len(
                rec.incident_ids
            )

    @api.depends('incident_ids.total_loss')
    def _compute_total_loss(self):

        for rec in self:
            rec.total_loss_amount = sum(
                rec.incident_ids.mapped(
                    'total_loss'
                )
            )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code(
                    'risk.risk'
                )

        return super().create(vals_list)

    def action_assess(self):
        """Ouvre l'assistant d'évaluation des risques"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Évaluation du risque',
            'res_model': 'risk.assessment',  # À adapter selon votre modèle
            'view_mode': 'form',
            'target': 'new',  # Ouvre en popup
            'context': {
                'default_risk_id': self.id,
            },
        }

    def action_close(self):
        """Ferme le risque"""
        for record in self:
            record.state = 'obsolete'
            record.active = False  # Si vous avez un champ actif
        return True

    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        if self.activity_id:
            self.process_id = self.activity_id.process_id
            self.macro_process_id = self.activity_id.macro_process_id