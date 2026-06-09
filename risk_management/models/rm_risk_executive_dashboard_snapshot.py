from odoo import models, fields, api


class RiskExecutiveDashboardSnapshot(models.Model):
    _name = 'risk.executive.dashboard.snapshot'
    _description = 'Executive Dashboard Snapshot'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'snapshot_date desc'

    name = fields.Char(
        required=True,
        tracking=True
    )

    snapshot_date = fields.Date(
        required=True,
        tracking=True
    )

    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company
    )

    ####################################################################
    # REFERENCES
    ####################################################################

    grc_score_id = fields.Many2one(
        'risk.grc.score'
    )

    grc_history_id = fields.Many2one(
        'risk.grc.history'
    )

    ####################################################################
    # EXECUTIVE SCORES
    ####################################################################

    overall_score = fields.Float()

    risk_score = fields.Float()

    compliance_score = fields.Float()

    audit_score = fields.Float()

    resilience_score = fields.Float()

    cyber_score = fields.Float()

    maturity_level = fields.Selection(
        [
            ('initial', 'Initial'),
            ('basic', 'Basic'),
            ('defined', 'Defined'),
            ('managed', 'Managed'),
            ('optimized', 'Optimized')
        ]
    )

    ####################################################################
    # RISKS
    ####################################################################

    total_risks = fields.Integer()

    critical_risks = fields.Integer()

    high_risks = fields.Integer()

    risks_over_appetite = fields.Integer()

    ####################################################################
    # INCIDENTS
    ####################################################################

    total_incidents = fields.Integer()

    open_incidents = fields.Integer()

    critical_incidents = fields.Integer()

    operational_losses = fields.Monetary()

    ####################################################################
    # AUDIT
    ####################################################################

    total_findings = fields.Integer()

    open_findings = fields.Integer()

    critical_findings = fields.Integer()

    overdue_audit_actions = fields.Integer()

    ####################################################################
    # COMPLIANCE
    ####################################################################

    compliance_rate = fields.Float()

    non_compliant_requirements = fields.Integer()

    overdue_compliance_actions = fields.Integer()

    ####################################################################
    # BCM / DRP
    ####################################################################

    bcp_coverage_rate = fields.Float()

    drp_coverage_rate = fields.Float()

    exercise_success_rate = fields.Float()

    ####################################################################
    # CRISIS MANAGEMENT
    ####################################################################

    crisis_count = fields.Integer()

    average_detection_time = fields.Float()

    average_recovery_time = fields.Float()

    average_closure_time = fields.Float()

    ####################################################################
    # HEATMAP
    ####################################################################

    heatmap_attachment_id = fields.Many2one(
        'ir.attachment'
    )

    ####################################################################
    # TOP RISKS
    ####################################################################

    top_risk_ids = fields.Many2many(
        'risk.risk',
        string='Top Risks'
    )

    ####################################################################
    # EXECUTIVE COMMENTARY
    ####################################################################

    executive_summary = fields.Html()

    key_changes = fields.Html()

    recommendations = fields.Html()

    ####################################################################
    # FINANCIAL
    ####################################################################

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self:
        self.env.company.currency_id
    )

    ####################################################################
    # STATE
    ####################################################################

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('validated', 'Validated'),
            ('published', 'Published')
        ],
        default='draft'
    )

    def action_validate(self):

        self.write({
            'state': 'validated'
        })

    def action_publish(self):

        self.write({
            'state': 'published'
        })