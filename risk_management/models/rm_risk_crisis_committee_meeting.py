from odoo import models, fields, api


class RiskCrisisCommitteeMeeting(models.Model):
    _name = 'risk.crisis.committee.meeting'
    _description = 'Crisis Committee Meeting'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]
    _order = 'meeting_date desc'

    name = fields.Char(
        readonly=True,
        default='New',
        tracking=True
    )

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True,
        ondelete='cascade'
    )

    title = fields.Char(
        required=True,
        tracking=True
    )

    meeting_date = fields.Datetime(
        required=True,
        tracking=True
    )

    location = fields.Char()

    chairman_id = fields.Many2one(
        'hr.employee',
        string='Chairman'
    )

    secretary_id = fields.Many2one(
        'hr.employee',
        string='Secretary'
    )

    agenda = fields.Html()

    minutes = fields.Html()

    decision_summary = fields.Html()

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments'
    )

    participant_ids = fields.One2many(
        'risk.crisis.committee.participant',
        'meeting_id'
    )

    decision_ids = fields.One2many(
        'risk.crisis.committee.decision',
        'meeting_id'
    )

    state = fields.Selection(
        [
            ('planned', 'Planned'),
            ('held', 'Held'),
            ('cancelled', 'Cancelled')
        ],
        default='planned',
        tracking=True
    )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('name', 'New') == 'New':

                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'risk.crisis.committee.meeting'
                )

        return super().create(vals_list)

    def action_hold(self):
        self.write({
            'state': 'held'
        })

    def action_cancel(self):
        self.write({
            'state': 'cancelled'
        })