from odoo import models, fields


class RiskDrpPlan(models.Model):
    _name = 'risk.drp.plan'
    _description = 'Disaster Recovery Plan'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    system_id = fields.Many2one(
        'risk.asset'
    )

    recovery_site_id = fields.Many2one(
        'risk.recovery.site'
    )

    recovery_procedure = fields.Html()

    backup_strategy = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved')
        ],
        default='draft'
    )