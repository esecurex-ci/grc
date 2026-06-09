from odoo import models, fields


class RiskCorrectiveAction(models.Model):
    _name = 'risk.corrective.action'
    _description = 'Corrective Action'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    incident_id = fields.Many2one(
        'risk.incident',
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

    due_date = fields.Date()

    completion_date = fields.Date()

    progress = fields.Float()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )

    def action_start(self):
        self.state = 'in_progress'

    def action_complete(self):
        self.state = 'completed'
        self.progress = 100

    def action_cancel(self):
        self.state = 'cancelled'