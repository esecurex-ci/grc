from odoo import models, fields, api


class RiskGrcScore(models.Model):
    _name = 'risk.grc.score'
    _description = 'Global GRC Score'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'assessment_date desc'

    name = fields.Char(
        required=True,
        default='New',
        readonly=True
    )

    assessment_date = fields.Date(
        default=fields.Date.today,
        required=True
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True
    )

    ####################################################################
    # DOMAIN SCORES
    ####################################################################

    risk_score = fields.Float(
        string='Risk Score'
    )

    control_score = fields.Float(
        string='Control Score'
    )

    audit_score = fields.Float(
        string='Audit Score'
    )

    compliance_score = fields.Float(
        string='Compliance Score'
    )

    resilience_score = fields.Float(
        string='Resilience Score'
    )

    cyber_score = fields.Float(
        string='Cyber Score'
    )

    ####################################################################
    # WEIGHTS
    ####################################################################

    risk_weight = fields.Float(default=25)

    control_weight = fields.Float(default=15)

    audit_weight = fields.Float(default=15)

    compliance_weight = fields.Float(default=20)

    resilience_weight = fields.Float(default=15)

    cyber_weight = fields.Float(default=10)

    ####################################################################
    # GLOBAL SCORE
    ####################################################################

    overall_score = fields.Float(
        compute='_compute_overall_score',
        store=True
    )

    maturity_level = fields.Selection(
        [
            ('initial', 'Initial'),
            ('basic', 'Basic'),
            ('defined', 'Defined'),
            ('managed', 'Managed'),
            ('optimized', 'Optimized')
        ],
        compute='_compute_maturity_level',
        store=True
    )

    comment = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('validated', 'Validated')
        ],
        default='draft'
    )

    @api.depends(
        'risk_score',
        'control_score',
        'audit_score',
        'compliance_score',
        'resilience_score',
        'cyber_score'
    )
    def _compute_overall_score(self):

        for rec in self:

            rec.overall_score = (

                (rec.risk_score * rec.risk_weight)

                +

                (rec.control_score * rec.control_weight)

                +

                (rec.audit_score * rec.audit_weight)

                +

                (rec.compliance_score * rec.compliance_weight)

                +

                (rec.resilience_score * rec.resilience_weight)

                +

                (rec.cyber_score * rec.cyber_weight)

            ) / 100

    @api.depends('overall_score')
    def _compute_maturity_level(self):

        for rec in self:

            if rec.overall_score >= 90:
                rec.maturity_level = 'optimized'

            elif rec.overall_score >= 75:
                rec.maturity_level = 'managed'

            elif rec.overall_score >= 60:
                rec.maturity_level = 'defined'

            elif rec.overall_score >= 40:
                rec.maturity_level = 'basic'

            else:
                rec.maturity_level = 'initial'