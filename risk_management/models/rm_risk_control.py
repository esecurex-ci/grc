from odoo import models, fields, api


class RiskControl(models.Model):
    _name = 'risk.control'
    _description = 'Risk Control'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code'

    name = fields.Char(
        required=True,
        tracking=True
    )

    code = fields.Char(
        required=True,
        tracking=True
    )

    description = fields.Html()

    objective = fields.Html()

    risk_ids = fields.Many2many(
        'risk.risk',
        string='Risks'
    )

    owner_id = fields.Many2one(
        'hr.employee',
        string='Control Owner'
    )

    control_type = fields.Selection(
        [
            ('preventive', 'Preventive'),
            ('detective', 'Detective'),
            ('corrective', 'Corrective')
        ],
        required=True
    )

    frequency = fields.Selection(
        [
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('semiannual', 'Semi Annual'),
            ('annual', 'Annual')
        ]
    )

    automation_level = fields.Selection(
        [
            ('manual', 'Manual'),
            ('semi_auto', 'Semi Automated'),
            ('automatic', 'Automated')
        ]
    )

    effectiveness = fields.Float(
        compute='_compute_effectiveness',
        store=True
    )

    active = fields.Boolean(default=True)

    test_ids = fields.One2many(
        'risk.control.test',
        'control_id'
    )
    compliance_requirement_ids = fields.Many2many(
        'risk.compliance.requirement',
        string='Compliance Requirements'
    )

    @api.depends('test_ids.result_score')
    def _compute_effectiveness(self):

        for rec in self:

            scores = rec.test_ids.mapped(
                'result_score'
            )

            rec.effectiveness = (
                sum(scores) / len(scores)
                if scores else 0
            )