from odoo import models, fields


class RiskHeatmapLine(models.Model):
    _name = 'risk.heatmap.line'
    _description = 'Risk Heatmap Line'

    heatmap_id = fields.Many2one(
        'risk.heatmap',
        required=True,
        ondelete='cascade'
    )

    risk_id = fields.Many2one(
        'risk.risk',
        required=True
    )

    assessment_id = fields.Many2one(
        'risk.assessment'
    )

    probability = fields.Integer()

    impact = fields.Integer()

    score = fields.Integer()

    risk_level = fields.Selection(
        [
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('important', 'Important'),
            ('high', 'High'),
            ('critical', 'Critical')
        ]
    )

    cell_code = fields.Char(
        compute='_compute_cell_code',
        store=True
    )

    color = fields.Char()

    def _compute_cell_code(self):

        for rec in self:

            rec.cell_code = (
                f"{rec.probability}"
                f"x"
                f"{rec.impact}"
            )