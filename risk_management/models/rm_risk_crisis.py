from odoo import models, fields, api


class RiskCrisis(models.Model):
    _name = 'risk.crisis'
    _description = 'Crisis Management'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        readonly=True,
        default='New'
    )

    title = fields.Char(
        required=True,
        tracking=True
    )

    scenario_id = fields.Many2one(
        'risk.crisis.scenario'
    )

    incident_id = fields.Many2one(
        'risk.incident'
    )

    declaration_date = fields.Datetime(
        default=fields.Datetime.now
    )

    start_date = fields.Datetime()

    end_date = fields.Datetime()

    crisis_level = fields.Selection(
        [
            ('minor', 'Minor'),
            ('major', 'Major'),
            ('critical', 'Critical')
        ],
        default='major'
    )

    crisis_manager_id = fields.Many2one(
        'hr.employee',
        string='Crisis Manager'
    )

    description = fields.Html()

    impact = fields.Html()

    state = fields.Selection(
        [
            ('declared', 'Declared'),
            ('activated', 'Activated'),
            ('managed', 'Managed'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed')
        ],
        default='declared',
        tracking=True
    )

    team_ids = fields.One2many(
        'risk.crisis.member',
        'crisis_id'
    )

    action_ids = fields.One2many(
        'risk.crisis.action',
        'crisis_id'
    )

    communication_ids = fields.One2many(
        'risk.crisis.communication',
        'crisis_id'
    )

    decision_ids = fields.One2many(
        'risk.crisis.decision',
        'crisis_id'
    )

    log_ids = fields.One2many(
        'risk.crisis.log',
        'crisis_id'
    )

    rex_id = fields.One2many(
        'risk.crisis.rex',
        'crisis_id'
    )
    regulator_notification_required = fields.Boolean()

    regulator_notification_date = fields.Datetime()

    regulator_reference = fields.Char()
    crisis_committee_meeting_ids = fields.One2many(
        'risk.crisis.committee.meeting',
        'crisis_id',
        string='Committee Meetings'
    )

    meeting_count = fields.Integer(
        compute='_compute_meeting_count'
    )

    @api.depends('crisis_committee_meeting_ids')
    def _compute_meeting_count(self):
        for rec in self:
            rec.meeting_count = len(
                rec.crisis_committee_meeting_ids
            )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('name', 'New') == 'New':

                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'risk.crisis'
                )

        return super().create(vals_list)

    def action_activate(self):
        self.state = 'activated'

    def action_manage(self):
        self.state = 'managed'

    def action_resolve(self):
        self.state = 'resolved'

    def action_close(self):
        self.state = 'closed'