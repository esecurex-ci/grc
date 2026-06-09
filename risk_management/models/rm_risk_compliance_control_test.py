from odoo import models, fields


class RiskComplianceControlTest(models.Model):
    _name = 'risk.compliance.control.test'
    _description = 'Compliance Control Test'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    requirement_id = fields.Many2one(
        'risk.compliance.requirement',
        required=True
    )

    control_id = fields.Many2one(
        'risk.control',
        required=True
    )

    test_date = fields.Date(
        required=True
    )

    tester_id = fields.Many2one(
        'hr.employee'
    )

    result = fields.Selection(
        [
            ('compliant', 'Compliant'),
            ('partially', 'Partially Compliant'),
            ('non_compliant', 'Non Compliant')
        ],
        required=True
    )

    score = fields.Float()

    observation = fields.Html()

    recommendation = fields.Html()