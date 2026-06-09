from odoo import models, fields


class RiskBcpPlan(models.Model):
    _name = 'risk.bcp.plan'
    _description = 'Business Continuity Plan'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    process_id = fields.Many2one(
        'risk.process'
    )

    owner_id = fields.Many2one(
        'hr.employee'
    )

    activation_criteria = fields.Html()

    recovery_strategy = fields.Html()

    communication_plan = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('obsolete', 'Obsolete')
        ],
        default='draft'
    )

    resource_ids = fields.One2many(
        'risk.bcp.resource',
        'bcp_id'
    )