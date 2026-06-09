from odoo import models, fields


class RiskCrisisCommitteeAction(models.Model):
    _name = 'risk.crisis.committee.action'
    _description = 'Committee Action'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    decision_id = fields.Many2one(
        'risk.crisis.committee.decision',
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
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )

    def action_start(self):
        self.state = 'in_progress'

    def action_complete(self):

        self.write({
            'state': 'completed',
            'progress': 100,
            'completion_date': fields.Date.today()
        })

    def action_cancel(self):
        self.state = 'cancelled'