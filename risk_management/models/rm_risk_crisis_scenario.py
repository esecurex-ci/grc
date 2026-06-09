from odoo import models, fields


class RiskCrisisScenario(models.Model):
    _name = 'risk.crisis.scenario'
    _description = 'Crisis Scenario'
    _inherit = ['mail.thread']

    name = fields.Char(
        required=True
    )

    category = fields.Selection(
        [
            ('cyber', 'Cyber Attack'),
            ('fire', 'Fire'),
            ('pandemic', 'Pandemic'),
            ('power', 'Power Outage'),
            ('flood', 'Flood'),
            ('supplier', 'Supplier Failure')
        ]
    )

    description = fields.Html()

    impact = fields.Html()

    response_strategy = fields.Html()