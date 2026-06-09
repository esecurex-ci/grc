from odoo import models, fields


class RiskControlTest(models.Model):
    _name = 'risk.control.test'
    _description = 'Control Test'
    _inherit = ['mail.thread']

    name = fields.Char(
        required=True
    )

    control_id = fields.Many2one(
        'risk.control',
        required=True,
        ondelete='cascade'
    )

    test_date = fields.Date(
        required=True,
        default=fields.Date.today
    )

    tester_id = fields.Many2one(
        'hr.employee'
    )

    sample_size = fields.Integer()

    error_count = fields.Integer()

    result_score = fields.Float()

    observation = fields.Html()

    result = fields.Selection(
        [
            ('effective', 'Effective'),
            ('partially', 'Partially Effective'),
            ('ineffective', 'Ineffective')
        ]
    )

    recommendation = fields.Html()