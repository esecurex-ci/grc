from odoo import models, fields

class RiskProcess(models.Model):
    _name = 'risk.process'
    _description = 'Business Process'

    name = fields.Char(required=True)

    code = fields.Char()

    owner_id = fields.Many2one(
        'hr.employee',
        string='Process Owner'
    )

    description = fields.Text()

    active = fields.Boolean(default=True)