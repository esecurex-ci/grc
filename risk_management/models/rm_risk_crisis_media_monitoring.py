from odoo import models, fields


class RiskCrisisMediaMonitoring(models.Model):
    _name = 'risk.crisis.media.monitoring'
    _description = 'Media Monitoring'
    _order = 'publication_date desc'

    crisis_id = fields.Many2one(
        'risk.crisis'
    )

    source = fields.Char()

    publication_date = fields.Datetime()

    title = fields.Char()

    url = fields.Char()

    sentiment = fields.Selection(
        [
            ('positive', 'Positive'),
            ('neutral', 'Neutral'),
            ('negative', 'Negative')
        ]
    )

    impact_level = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High')
        ]
    )

    summary = fields.Html()