from odoo import models, fields


class RiskComplianceRequirement(models.Model):
    _name = 'risk.compliance.requirement'
    _description = 'Compliance Requirement'
    _inherit = ['mail.thread']

    code = fields.Char(
        required=True
    )

    title = fields.Char(
        required=True
    )

    framework_id = fields.Many2one(
        'risk.compliance.framework',
        required=True,
        ondelete='cascade'
    )

    article = fields.Char()

    description = fields.Html()

    mandatory = fields.Boolean(
        default=True
    )

    risk_ids = fields.Many2many(
        'risk.risk',
        string='Related Risks'
    )

    control_ids = fields.Many2many(
        'risk.control',
        string='Controls'
    )

    audit_finding_ids = fields.Many2many(
        'risk.audit.finding',
        string='Audit Findings'
    )

    active = fields.Boolean(
        default=True
    )
    mapping_ids = fields.One2many(
        'risk.compliance.mapping',
        'requirement_id'
    )

    control_test_ids = fields.One2many(
        'risk.compliance.control.test',
        'requirement_id'
    )