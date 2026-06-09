from odoo import models, fields


class RiskComplianceActionPlan(models.Model):
    _name = 'risk.compliance.action.plan'
    _description = 'Compliance Action Plan'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    assessment_id = fields.Many2one(
        'risk.compliance.assessment',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        required=True
    )

    description = fields.Html()

    owner_id = fields.Many2one(
        'hr.employee'
    )

    target_date = fields.Date()

    completion_date = fields.Date()

    progress = fields.Float()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('validated', 'Validated')
        ],
        default='draft'
    )

    def action_start(self):
        self.state = 'in_progress'

    def action_complete(self):
        self.state = 'completed'
        self.progress = 100

    def action_validate(self):
        self.state = 'validated'