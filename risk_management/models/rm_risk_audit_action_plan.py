from odoo import models, fields


class RiskAuditActionPlan(models.Model):
    _name = 'risk.audit.action.plan'
    _description = 'Audit Action Plan'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    recommendation_id = fields.Many2one(
        'risk.audit.recommendation',
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

    start_date = fields.Date()

    target_date = fields.Date()

    completion_date = fields.Date()

    progress = fields.Float()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('validated', 'Validated'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment'
    )

    def action_start(self):
        self.state = 'in_progress'

    def action_complete(self):
        self.state = 'completed'
        self.progress = 100

    def action_validate(self):
        self.state = 'validated'

    def action_cancel(self):
        self.state = 'cancelled'