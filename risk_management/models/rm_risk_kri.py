from odoo import models, fields, api


class RiskKri(models.Model):
    _name = 'risk.kri'
    _description = 'Key Risk Indicator'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        required=True
    )

    code = fields.Char()

    description = fields.Html()

    risk_ids = fields.Many2many(
        'risk.risk'
    )

    owner_id = fields.Many2one(
        'hr.employee'
    )

    unit = fields.Char(
        default='%'
    )

    threshold_green = fields.Float()

    threshold_amber = fields.Float()

    threshold_red = fields.Float()

    current_value = fields.Float(
        compute='_compute_current_value',
        store=True
    )

    status = fields.Selection(
        [
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red')
        ],
        compute='_compute_status',
        store=True
    )

    measure_ids = fields.One2many(
        'risk.kri.measure',
        'kri_id'
    )

    # Dans rm_risk_kri.py, ajoutez :
    activity_id = fields.Many2one(
        'risk.activity',
        string='Activité',
        ondelete='set null'
    )


    @api.depends(
        'measure_ids.value'
    )
    def _compute_current_value(self):

        for rec in self:

            latest = rec.measure_ids.sorted(
                'measure_date',
                reverse=True
            )[:1]

            rec.current_value = (
                latest.value
                if latest else 0
            )

    @api.depends(
        'current_value',
        'threshold_green',
        'threshold_amber',
        'threshold_red'
    )
    def _compute_status(self):

        for rec in self:

            if rec.current_value >= rec.threshold_red:
                rec.status = 'red'

            elif rec.current_value >= rec.threshold_amber:
                rec.status = 'amber'

            else:
                rec.status = 'green'