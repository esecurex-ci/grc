from odoo import models, fields


class RiskTreatmentPlan(models.Model):
    _name = 'risk.treatment.plan'
    _description = 'Risk Treatment Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        required=True
    )

    assessment_id = fields.Many2one(
        'risk.assessment',
        required=True,
        ondelete='cascade'
    )

    risk_id = fields.Many2one(
        related='assessment_id.risk_id',
        store=True
    )

    owner_id = fields.Many2one(
        'hr.employee',
        string='Action Owner'
    )

    description = fields.Html()

    target_date = fields.Date()

    budget = fields.Monetary()

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self:
        self.env.company.currency_id
    )

    progress = fields.Float(
        default=0
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )

    completion_date = fields.Date()

    active = fields.Boolean(
        default=True
    )

    def action_start(self):
        self.write({
            'state': 'in_progress'
        })

    def action_complete(self):
        self.write({
            'state': 'completed',
            'progress': 100,
            'completion_date': fields.Date.today()
        })

    def action_cancel(self):
        self.write({
            'state': 'cancelled'
        })
