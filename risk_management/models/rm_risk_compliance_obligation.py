from odoo import models, fields


class RiskComplianceObligation(models.Model):
    _name = 'risk.compliance.obligation'
    _description = 'Compliance Obligation'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    requirement_id = fields.Many2one(
        'risk.compliance.requirement',
        required=True,
        ondelete='cascade'
    )

    owner_id = fields.Many2one(
        'hr.employee'
    )

    process_ids = fields.Many2many(
        'risk.process'
    )

    organization_ids = fields.Many2many(
        'risk.organization'
    )

    frequency = fields.Selection(
        [
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('annual', 'Annual')
        ]
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('obsolete', 'Obsolete')
        ],
        default='active'
    )

    description = fields.Html()