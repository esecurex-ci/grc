from odoo import models, fields


class RiskAuditPlan(models.Model):
    _name = 'risk.audit.plan'
    _description = 'Audit Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        required=True
    )

    year = fields.Integer(
        required=True
    )

    description = fields.Html()

    owner_id = fields.Many2one(
        'hr.employee'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('closed', 'Closed')
        ],
        default='draft'
    )

    audit_ids = fields.One2many(
        'risk.audit',
        'plan_id'
    )

    def action_approve(self):
        self.state = 'approved'

    def action_close(self):
        self.state = 'closed'