from odoo import models, fields, api


class RiskComplianceScorecard(models.Model):
    _name = 'risk.compliance.scorecard'
    _description = 'Compliance Scorecard'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]
    _order = 'reference_date desc'

    name = fields.Char(
        required=True,
        tracking=True
    )

    reference_date = fields.Date(
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('validated', 'Validated')
        ],
        default='draft',
        tracking=True
    )

    # Référentiel
    requirement_count = fields.Integer(
        compute='_compute_kpis'
    )

    mandatory_requirement_count = fields.Integer(
        compute='_compute_kpis'
    )

    # Conformité

    compliant_count = fields.Integer(
        compute='_compute_kpis'
    )

    partial_count = fields.Integer(
        compute='_compute_kpis'
    )

    non_compliant_count = fields.Integer(
        compute='_compute_kpis'
    )

    compliance_rate = fields.Float(
        compute='_compute_kpis'
    )

    # Obligations

    obligation_count = fields.Integer(
        compute='_compute_kpis'
    )

    overdue_obligation_count = fields.Integer(
        compute='_compute_kpis'
    )

    # Actions

    action_plan_count = fields.Integer(
        compute='_compute_kpis'
    )

    overdue_action_plan_count = fields.Integer(
        compute='_compute_kpis'
    )

    # Preuves

    evidence_count = fields.Integer(
        compute='_compute_kpis'
    )

    # Risque conformité

    compliance_risk_score = fields.Float(
        compute='_compute_kpis'
    )

    compliance_level = fields.Selection(
        [
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('average', 'Average'),
            ('poor', 'Poor')
        ],
        compute='_compute_kpis'
    )
    line_ids = fields.One2many(
        'risk.compliance.scorecard.line',
        'scorecard_id',
        string='Details'
    )

    framework_count = fields.Integer(
        compute='_compute_framework_count'
    )

    @api.depends('line_ids')
    def _compute_framework_count(self):

        for rec in self:
            rec.framework_count = len(
                rec.line_ids
            )

    @api.depends('reference_date')
    def _compute_kpis(self):

        framework_obj = self.env[
            'risk.compliance.framework'
        ]

        requirement_obj = self.env[
            'risk.compliance.requirement'
        ]

        assessment_obj = self.env[
            'risk.compliance.assessment'
        ]

        obligation_obj = self.env[
            'risk.compliance.obligation'
        ]

        evidence_obj = self.env[
            'risk.compliance.evidence'
        ]

        action_obj = self.env[
            'risk.compliance.action.plan'
        ]

        for rec in self:

            rec.framework_count = framework_obj.search_count([])

            rec.requirement_count = requirement_obj.search_count([])

            rec.mandatory_requirement_count = (
                requirement_obj.search_count([
                    ('mandatory', '=', True)
                ])
            )

            rec.compliant_count = (
                assessment_obj.search_count([
                    ('compliance_level', '=', 'compliant')
                ])
            )

            rec.partial_count = (
                assessment_obj.search_count([
                    ('compliance_level', '=', 'partially')
                ])
            )

            rec.non_compliant_count = (
                assessment_obj.search_count([
                    ('compliance_level', '=', 'non_compliant')
                ])
            )

            total = (
                rec.compliant_count +
                rec.partial_count +
                rec.non_compliant_count
            )

            rec.compliance_rate = (
                rec.compliant_count * 100 / total
                if total else 0
            )

            rec.obligation_count = (
                obligation_obj.search_count([])
            )

            rec.action_plan_count = (
                action_obj.search_count([])
            )

            rec.evidence_count = (
                evidence_obj.search_count([])
            )

            rec.overdue_action_plan_count = (
                action_obj.search_count([
                    ('target_date', '<', fields.Date.today()),
                    ('state', '!=', 'validated')
                ])
            )

            rec.overdue_obligation_count = (
                obligation_obj.search_count([
                    ('next_due_date', '<', fields.Date.today())
                ])
            )

            rec.compliance_risk_score = (
                rec.non_compliant_count * 10
            )

            if rec.compliance_rate >= 95:
                rec.compliance_level = 'excellent'

            elif rec.compliance_rate >= 85:
                rec.compliance_level = 'good'

            elif rec.compliance_rate >= 70:
                rec.compliance_level = 'average'

            else:
                rec.compliance_level = 'poor'