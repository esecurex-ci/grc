from odoo import models, fields


class RiskKriMeasure(models.Model):
    _name = 'risk.kri.measure'
    _description = 'KRI Measure'

    kri_id = fields.Many2one(
        'risk.kri',
        required=True,
        ondelete='cascade'
    )

    measure_date = fields.Date(
        required=True
    )

    value = fields.Float(
        required=True
    )

    comment = fields.Html()