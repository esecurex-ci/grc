from odoo import models, fields


class RiskRegulatoryChangeAction(models.Model):
    _name = 'risk.regulatory.change.action'
    _description = 'Regulatory Change Action'

    change_id = fields.Many2one(
        'risk.regulatory.change',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        required=True
    )

    owner_id = fields.Many2one(
        'hr.employee'
    )

    due_date = fields.Date()

    progress = fields.Float()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed')
        ],
        default='draft'
    )