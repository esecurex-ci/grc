from odoo import models, fields, api


class RiskCrisisDashboard(models.Model):
    _name = 'risk.crisis.dashboard'
    _description = 'Crisis Dashboard'
    _rec_name = 'name'

    name = fields.Char(
        default='Crisis Dashboard'
    )

    snapshot_date = fields.Date(
        default=fields.Date.today
    )

    # KPI Crises

    open_crisis_count = fields.Integer(
        compute='_compute_dashboard'
    )

    critical_crisis_count = fields.Integer(
        compute='_compute_dashboard'
    )

    mttr_hours = fields.Float(
        string='MTTR (Hours)',
        compute='_compute_dashboard'
    )

    # Gouvernance

    committee_meeting_count = fields.Integer(
        compute='_compute_dashboard'
    )

    overdue_decision_count = fields.Integer(
        compute='_compute_dashboard'
    )

    # Actions

    open_action_count = fields.Integer(
        compute='_compute_dashboard'
    )

    # Communication

    regulator_communication_count = fields.Integer(
        compute='_compute_dashboard'
    )

    # Retour d'expérience

    closed_rex_count = fields.Integer(
        compute='_compute_dashboard'
    )

    # Indicateur global

    crisis_management_score = fields.Float(
        compute='_compute_dashboard'
    )

    dashboard_level = fields.Selection(
        [
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('average', 'Average'),
            ('critical', 'Critical')
        ],
        compute='_compute_dashboard'
    )
    line_ids = fields.One2many(
        'risk.crisis.dashboard.line',
        'dashboard_id',
        string='Crises'
    )

    crisis_count = fields.Integer(
        compute='_compute_crisis_count'
    )

    @api.depends('line_ids')
    def _compute_crisis_count(self):

        for rec in self:
            rec.crisis_count = len(
                rec.line_ids
            )

    @api.depends('snapshot_date')
    def _compute_dashboard(self):

        Crisis = self.env['risk.crisis']

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

        Rex = self.env[
            'risk.crisis.rex'
        ]

        for rec in self:

            crises = Crisis.search([])

            open_crises = crises.filtered(
                lambda c:
                c.state not in ('closed',)
            )

            rec.open_crisis_count = len(
                open_crises
            )

            rec.critical_crisis_count = len(
                crises.filtered(
                    lambda c:
                    c.crisis_level == 'critical'
                    and c.state != 'closed'
                )
            )

            resolved = crises.filtered(
                lambda c:
                c.start_date and
                c.end_date
            )

            if resolved:

                durations = []

                for crisis in resolved:

                    duration = (
                        crisis.end_date -
                        crisis.start_date
                    ).total_seconds() / 3600

                    durations.append(duration)

                rec.mttr_hours = (
                    sum(durations) /
                    len(durations)
                )

            else:

                rec.mttr_hours = 0

            rec.committee_meeting_count = (
                Meeting.search_count([])
            )

            rec.overdue_decision_count = (
                Decision.search_count([
                    ('due_date', '<', fields.Date.today()),
                    ('state', '!=', 'closed')
                ])
            )

            rec.open_action_count = (
                Action.search_count([
                    ('state', 'not in',
                     ['completed', 'cancelled'])
                ])
            )

            rec.regulator_communication_count = (
                Communication.search_count([
                    ('audience', '=', 'regulator')
                ])
            )

            rec.closed_rex_count = (
                Rex.search_count([
                    ('completion_status', '=',
                     'implemented')
                ])
            )

            score = 100

            score -= (
                rec.critical_crisis_count * 5
            )

            score -= (
                rec.overdue_decision_count * 3
            )

            score -= (
                rec.open_action_count * 1
            )

            rec.crisis_management_score = max(
                score,
                0
            )

            if rec.crisis_management_score >= 90:

                rec.dashboard_level = 'excellent'

            elif rec.crisis_management_score >= 75:

                rec.dashboard_level = 'good'

            elif rec.crisis_management_score >= 50:

                rec.dashboard_level = 'average'

            else:

                rec.dashboard_level = 'critical'

    def action_refresh(self):
        self._compute_dashboard()