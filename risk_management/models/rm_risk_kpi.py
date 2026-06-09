from odoo import models, fields


class RiskKpi(models.Model):
    _name = 'risk.kpi'
    _description = 'Enterprise KPI'

    name = fields.Char(
        required=True
    )

    code = fields.Char()

    owner_id = fields.Many2one(
        'hr.employee'
    )

    target_value = fields.Float()

    current_value = fields.Float()

    unit = fields.Char()

    measure_ids = fields.One2many(
        'risk.kpi.measure',
        'kpi_id'
    )