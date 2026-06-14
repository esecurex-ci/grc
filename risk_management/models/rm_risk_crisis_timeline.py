from odoo import models, fields


class RiskCrisisTimeline(models.Model):
    _name = 'risk.crisis.timeline'
    _description = 'Crisis Timeline'
    _order = 'event_date'

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True
    )

    event_date = fields.Datetime(
        required=True
    )

    event_type = fields.Selection(
        [
            ('detection', 'Detection'),
            ('decision', 'Decision'),
            ('communication', 'Communication'),
            ('action', 'Action'),
            ('resolution', 'Resolution')
        ]
    )

    title = fields.Char(
        required=True
    )

    description = fields.Html()

    owner_id = fields.Many2one(
        'hr.employee'
    )

    command_center_id = fields.Many2one(
        'risk.crisis.command.center',
        string='Command Center',
        ondelete='cascade',
        index=True,
        help='Centre de commandement associé'
    )

    is_recent = fields.Boolean(
        string='Is Recent',
        default=True
    )

    def _compute_is_recent(self):
        for record in self:
            if record.event_datetime:
                from datetime import timedelta
                days_diff = (fields.Datetime.now() - record.event_datetime).days
                record.is_recent = days_diff <= 7
            else:
                record.is_recent = False

    event_datetime = fields.Datetime(
        string='Event Date',
        required=True
    )