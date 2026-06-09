from odoo import models, fields


class RiskHeatmapSnapshot(models.Model):
    _name = 'risk.heatmap.snapshot'
    _description = 'Heatmap Snapshot'

    name = fields.Char()

    snapshot_date = fields.Date()

    assessment_period_id = fields.Many2one(
        'risk.assessment.period'
    )

    attachment_id = fields.Many2one(
        'ir.attachment'
    )