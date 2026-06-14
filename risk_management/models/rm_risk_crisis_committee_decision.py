from odoo import models, fields


class RiskCrisisCommitteeDecision(models.Model):
    _name = 'risk.crisis.committee.decision'
    _description = 'Committee Decision'

    meeting_id = fields.Many2one(
        'risk.crisis.committee.meeting',
        required=True,
        ondelete='cascade'
    )

    title = fields.Char(
        required=True
    )

    description = fields.Html()

    owner_id = fields.Many2one(
        'hr.employee'
    )

    due_date = fields.Date()

    action_ids = fields.One2many(
        'risk.crisis.committee.action',
        'decision_id'
    )

    state = fields.Selection(
        [
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('closed', 'Closed')
        ],
        default='open'
    )

    # ⬇️ CE CHAMP EST OBLIGATOIRE ⬇️
    crisis_id = fields.Many2one(
        'risk.crisis',
        string='Crisis',
        required=True,
        ondelete='cascade'
    )

    # ⬇️ CHAMP SOUVENT MANQUANT ⬇️
    deadline = fields.Date(
        string='Deadline',
        help='Date limite pour réaliser l\'action'
    )