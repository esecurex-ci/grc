from odoo import models, fields


class RiskIncidentType(models.Model):
    _name = 'risk.incident.type'
    _description = 'Incident Type'

    name = fields.Char(
        required=True
    )

    category_id = fields.Many2one(
        'risk.incident.category',
        required=True,
        ondelete='restrict'
    )

    description = fields.Text()

    active = fields.Boolean(
        default=True
    )