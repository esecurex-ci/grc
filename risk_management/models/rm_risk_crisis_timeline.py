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