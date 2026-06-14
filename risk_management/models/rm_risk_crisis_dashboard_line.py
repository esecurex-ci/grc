from odoo import models, fields, api


class RiskCrisisDashboardLine(models.Model):
    _name = 'risk.crisis.dashboard.line'
    _description = 'Crisis Dashboard Line'
    _order = 'crisis_start_date desc'

    dashboard_id = fields.Many2one(
        'risk.crisis.dashboard',
        required=True,
        ondelete='cascade'
    )

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True
    )

    crisis_name = fields.Char(
        related='crisis_id.name',
        store=True
    )

    crisis_level = fields.Selection(
        related='crisis_id.crisis_level',
        store=True
    )

    state = fields.Selection(
        related='crisis_id.state',
        store=True
    )

    crisis_manager_id = fields.Many2one(
        related='crisis_id.crisis_manager_id',
        store=True
    )

    crisis_start_date = fields.Datetime(
        related='crisis_id.start_date',
        store=True
    )

    crisis_end_date = fields.Datetime(
        related='crisis_id.end_date',
        store=True
    )

    duration_hours = fields.Float(
        compute='_compute_statistics',
        store=True
    )

    meeting_count = fields.Integer(
        compute='_compute_statistics',
        store=True
    )

    decision_count = fields.Integer(
        compute='_compute_statistics',
        store=True
    )

    overdue_decision_count = fields.Integer(
        compute='_compute_statistics',
        store=True
    )

    open_action_count = fields.Integer(
        compute='_compute_statistics',
        store=True
    )

    communication_count = fields.Integer(
        compute='_compute_statistics',
        store=True
    )

    regulator_communication_count = fields.Integer(
        compute='_compute_statistics',
        store=True
    )

    log_count = fields.Integer(
        compute='_compute_statistics',
        store=True
    )

    score = fields.Float(
        compute='_compute_statistics',
        store=True
    )

    # ⬇️ AJOUTEZ CE CHAMP ⬇️
    crisis_manager_id = fields.Many2one(
        'hr.employee',
        string='Crisis Manager',
        help='Person responsible for managing this crisis',
        tracking=True
    )

    performance_level = fields.Selection(
        [
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('average', 'Average'),
            ('critical', 'Critical')
        ],
        compute='_compute_statistics',
        store=True
    )

    @api.depends(
        'crisis_id',
        'crisis_id.state',
        'crisis_id.start_date',
        'crisis_id.end_date'
    )
    def _compute_statistics(self):

        Meeting = self.env[
            'risk.crisis.committee.meeting'
        ]

        Decision = self.env[
            'risk.crisis.committee.decision'
        ]

        Action = self.env[
            'risk.crisis.action'
        ]

        Communication = self.env[
            'risk.crisis.communication'
        ]

        Log = self.env[
            'risk.crisis.log'
        ]

        for rec in self:

            rec.duration_hours = 0

            if (
                rec.crisis_start_date and
                rec.crisis_end_date
            ):

                rec.duration_hours = (
                    (
                        rec.crisis_end_date -
                        rec.crisis_start_date
                    ).total_seconds()
                    / 3600
                )

            rec.meeting_count = Meeting.search_count([
                ('crisis_id', '=', rec.crisis_id.id)
            ])

            rec.decision_count = Decision.search_count([
                ('crisis_id', '=', rec.crisis_id.id)
            ])

            rec.overdue_decision_count = Decision.search_count([
                ('crisis_id', '=', rec.crisis_id.id),
                ('due_date', '<', fields.Date.today()),
                ('state', '!=', 'closed')
            ])

            rec.open_action_count = Action.search_count([
                ('crisis_id', '=', rec.crisis_id.id),
                ('state', 'not in',
                 ['completed', 'cancelled'])
            ])

            rec.communication_count = Communication.search_count([
                ('crisis_id', '=', rec.crisis_id.id)
            ])

            rec.regulator_communication_count = (
                Communication.search_count([
                    ('crisis_id', '=', rec.crisis_id.id),
                    ('audience', '=', 'regulator')
                ])
            )

            rec.log_count = Log.search_count([
                ('crisis_id', '=', rec.crisis_id.id)
            ])

            score = 100

            score -= (
                rec.overdue_decision_count * 5
            )

            score -= (
                rec.open_action_count * 2
            )

            score -= (
                rec.duration_hours / 24
            )

            rec.score = max(score, 0)

            if rec.score >= 90:

                rec.performance_level = 'excellent'

            elif rec.score >= 75:

                rec.performance_level = 'good'

            elif rec.score >= 50:

                rec.performance_level = 'average'

            else:

                rec.performance_level = 'critical'