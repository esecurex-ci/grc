from odoo import models, fields


class RiskExercise(models.Model):
    _name = 'risk.exercise'
    _description = 'BCP/DRP Exercise'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    exercise_date = fields.Date()

    exercise_type = fields.Selection(
        [
            ('tabletop', 'Table Top'),
            ('simulation', 'Simulation'),
            ('full_scale', 'Full Scale')
        ]
    )

    scenario_id = fields.Many2one(
        'risk.crisis.scenario'
    )

    objective = fields.Html()

    result = fields.Html()

    state = fields.Selection(
        [
            ('planned', 'Planned'),
            ('completed', 'Completed')
        ],
        default='planned'
    )

    finding_ids = fields.One2many(
        'risk.exercise.finding',
        'exercise_id'
    )