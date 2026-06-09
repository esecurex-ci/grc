from odoo import models, fields


class RiskCrisisMember(models.Model):
    _name = 'risk.crisis.member'
    _description = 'Crisis Team Member'

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True,
        ondelete='cascade'
    )

    employee_id = fields.Many2one(
        'hr.employee',
        required=True
    )

    role = fields.Selection(
        [
            ('manager', 'Crisis Manager'),
            ('it', 'IT Lead'),
            ('security', 'Security Officer'),
            ('compliance', 'Compliance Officer'),
            ('communication', 'Communication Lead'),
            ('business', 'Business Representative')
        ]
    )

    mobile = fields.Char()

    email = fields.Char()