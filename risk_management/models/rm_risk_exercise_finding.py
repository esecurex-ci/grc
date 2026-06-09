from odoo import models, fields


class RiskExerciseFinding(models.Model):
    _name = 'risk.exercise.finding'
    _description = 'Exercise Finding'

    exercise_id = fields.Many2one(
        'risk.exercise',
        required=True,
        ondelete='cascade'
    )

    description = fields.Html()

    severity = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical')
        ]
    )

    recommendation = fields.Html()