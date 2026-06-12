from odoo import models, fields, api


class RiskBcpPlan(models.Model):
    _name = 'risk.bcp.plan'
    _description = 'Business Continuity Plan'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    process_id = fields.Many2one(
        'risk.process'
    )

    owner_id = fields.Many2one(
        'hr.employee'
    )

    activation_criteria = fields.Html()

    recovery_strategy = fields.Html()

    communication_plan = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('obsolete', 'Obsolete')
        ],
        default='draft'
    )

    resource_ids = fields.One2many(
        'risk.bcp.resource',
        'bcp_id'
    )
    resource_count = fields.Integer(
        compute='_compute_resource_count'
    )

    @api.depends('resource_ids')
    def _compute_resource_count(self):
        for rec in self:
            rec.resource_count = len(
                rec.resource_ids
            )

    def action_view_resources(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Resources',
            'res_model': 'risk.bcp.resource',
            'view_mode': 'list,form',
            'domain': [
                ('bcp_id', '=', self.id)
            ],
            'context': {
                'default_bcp_id': self.id
            }
        }