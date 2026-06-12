from odoo import models, fields


class RiskCrisisHeatmap(models.Model):
    _name = 'risk.crisis.heatmap'
    _description = 'Crisis Heatmap'

    name = fields.Char(
        required=True
    )

    scenario_id = fields.Many2one(
        'risk.crisis.scenario',
        required=True
    )

    likelihood = fields.Selection(
        [
            ('1', 'Very Low'),
            ('2', 'Low'),
            ('3', 'Medium'),
            ('4', 'High'),
            ('5', 'Very High')
        ],
        required=True
    )

    impact = fields.Selection(
        [
            ('1', 'Very Low'),
            ('2', 'Low'),
            ('3', 'Medium'),
            ('4', 'High'),
            ('5', 'Very High')
        ],
        required=True
    )

    score = fields.Integer()

    risk_level = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical')
        ]
    )