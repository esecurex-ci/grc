from odoo import models, fields


class RiskGrcHistoryLine(models.Model):
    _name = 'risk.grc.history.line'
    _description = 'GRC History Detail'

    history_id = fields.Many2one(
        'risk.grc.history',
        required=True,
        ondelete='cascade'
    )

    metric_code = fields.Char(
        required=True
    )

    metric_name = fields.Char(
        required=True
    )

    metric_value = fields.Float()

    metric_target = fields.Float()

    variance = fields.Float()