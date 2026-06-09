from odoo import models, fields


class RiskCrisisRex(models.Model):
    _name = 'risk.crisis.rex'
    _description = 'Crisis Lessons Learned'
    _inherit = ['mail.thread']

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True,
        ondelete='cascade'
    )

    strengths = fields.Html()

    weaknesses = fields.Html()

    recommendations = fields.Html()

    action_plan = fields.Html()

    completion_status = fields.Selection(
        [
            ('open', 'Open'),
            ('implemented', 'Implemented')
        ],
        default='open'
    )