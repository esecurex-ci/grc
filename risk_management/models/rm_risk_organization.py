from odoo import models, fields

class RiskOrganization(models.Model):
    _name = 'risk.organization'
    _description = 'Organization Unit'

    name = fields.Char(required=True)

    code = fields.Char()

    manager_id = fields.Many2one(
        'hr.employee'
    )

    description = fields.Text()

    active = fields.Boolean(default=True)