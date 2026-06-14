from odoo import models, fields


class RiskCrisisAction(models.Model):
    _name = 'risk.crisis.action'
    _description = 'Crisis Action'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    crisis_id = fields.Many2one(
        'risk.crisis',
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

    due_date = fields.Datetime()

    completion_date = fields.Datetime()

    progress = fields.Float()

    state = fields.Selection(
        [
            ('planned', 'Planned'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='planned'
    )

    # ⬇️ CHAMP SOUVENT MANQUANT ⬇️
    deadline = fields.Date(
        string='Deadline',
        help='Date limite pour réaliser l\'action'
    )