from odoo import models, fields


class RiskIncidentCategory(models.Model):
    _name = 'risk.incident.category'
    _description = 'Incident Category'
    _order = 'name'

    name = fields.Char(
        required=True
    )

    code = fields.Char()

    description = fields.Text()

    active = fields.Boolean(
        default=True
    )