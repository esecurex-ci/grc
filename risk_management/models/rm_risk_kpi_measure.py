from odoo import models, fields


class RiskKpiMeasure(models.Model):
    _name = 'risk.kpi.measure'
    _description = 'KPI Measurement'

    kpi_id = fields.Many2one(
        'risk.kpi',
        required=True
    )

    measure_date = fields.Date()

    value = fields.Float()

    comment = fields.Html()