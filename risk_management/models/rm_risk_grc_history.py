from odoo import models, fields, api


class RiskGrcHistory(models.Model):
    _name = 'risk.grc.history'
    _description = 'GRC History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_date desc'

    name = fields.Char(
        required=True,
        tracking=True
    )

    period_date = fields.Date(
        required=True,
        tracking=True
    )

    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company
    )

    #################################################################
    # REFERENCES
    #################################################################

    grc_score_id = fields.Many2one(
        'risk.grc.score',
        string='GRC Score'
    )

    #################################################################
    # SCORES
    #################################################################

    overall_score = fields.Float(
        tracking=True
    )

    risk_score = fields.Float()

    control_score = fields.Float()

    audit_score = fields.Float()

    compliance_score = fields.Float()

    resilience_score = fields.Float()

    cyber_score = fields.Float()

    #################################################################
    # TREND ANALYSIS
    #################################################################

    previous_history_id = fields.Many2one(
        'risk.grc.history',
        string='Previous Period'
    )

    score_variation = fields.Float(
        compute='_compute_variation',
        store=True
    )

    trend = fields.Selection(
        [
            ('up', 'Improving'),
            ('stable', 'Stable'),
            ('down', 'Degrading')
        ],
        compute='_compute_variation',
        store=True
    )

    #################################################################
    # KPI SNAPSHOTS
    #################################################################

    total_risks = fields.Integer()

    critical_risks = fields.Integer()

    risks_over_appetite = fields.Integer()

    open_incidents = fields.Integer()

    operational_losses = fields.Monetary()

    open_findings = fields.Integer()

    overdue_actions = fields.Integer()

    compliance_rate = fields.Float()

    bcp_coverage_rate = fields.Float()

    drp_coverage_rate = fields.Float()

    crisis_exercises_rate = fields.Float()

    #################################################################
    # FINANCIAL
    #################################################################

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self:
        self.env.company.currency_id.id
    )

    #################################################################
    # MATURITY
    #################################################################

    maturity_level = fields.Selection(
        [
            ('initial', 'Initial'),
            ('basic', 'Basic'),
            ('defined', 'Defined'),
            ('managed', 'Managed'),
            ('optimized', 'Optimized')
        ]
    )

    comment = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('validated', 'Validated')
        ],
        default='draft',
        tracking=True
    )

    @api.depends(
        'overall_score',
        'previous_history_id.overall_score'
    )
    def _compute_variation(self):

        for rec in self:

            if not rec.previous_history_id:

                rec.score_variation = 0
                rec.trend = 'stable'
                continue

            variation = (
                rec.overall_score
                -
                rec.previous_history_id.overall_score
            )

            rec.score_variation = variation

            if variation > 0:
                rec.trend = 'up'

            elif variation < 0:
                rec.trend = 'down'

            else:
                rec.trend = 'stable'

    def action_validate(self):

        self.write({
            'state': 'validated'
        })