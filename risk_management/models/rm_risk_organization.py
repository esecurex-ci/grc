from odoo import models, fields

class RiskOrganization(models.Model):
    _name = 'risk.organization'
    _description = 'Unité organisationnelle'

    name = fields.Char(string='Nom', required=True)

    code = fields.Char(string='Code')

    manager_id = fields.Many2one(
        'hr.employee',
        string='Responsable'
    )

    description = fields.Text(string='Description')

    active = fields.Boolean(string='Actif', default=True)
