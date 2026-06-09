from odoo import models, fields


class RiskCrisisCommitteeParticipant(models.Model):
    _name = 'risk.crisis.committee.participant'
    _description = 'Committee Participant'

    meeting_id = fields.Many2one(
        'risk.crisis.committee.meeting',
        required=True,
        ondelete='cascade'
    )

    employee_id = fields.Many2one(
        'hr.employee',
        required=True
    )

    role = fields.Selection(
        [
            ('chairman', 'Chairman'),
            ('secretary', 'Secretary'),
            ('member', 'Member'),
            ('observer', 'Observer')
        ],
        default='member'
    )

    present = fields.Boolean(
        default=True
    )

    comment = fields.Text()