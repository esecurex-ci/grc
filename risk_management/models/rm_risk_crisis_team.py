from odoo import models, fields


class RiskCrisisTeam(models.Model):
    _name = 'risk.crisis.team'
    _description = 'Crisis Team'

    name = fields.Char(
        required=True
    )

    description = fields.Html()

    active = fields.Boolean(
        default=True
    )