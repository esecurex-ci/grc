from odoo import models, fields


class RiskRegulatoryChange(models.Model):
    _name = 'risk.regulatory.change'
    _description = 'Regulatory Change'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    framework_id = fields.Many2one(
        'risk.compliance.framework'
    )

    publication_date = fields.Date()

    effective_date = fields.Date()

    source = fields.Char()

    summary = fields.Html()

    impact_analysis = fields.Html()

    owner_id = fields.Many2one(
        'hr.employee'
    )

    state = fields.Selection(
        [
            ('identified', 'Identified'),
            ('analysis', 'Impact Analysis'),
            ('implementation', 'Implementation'),
            ('completed', 'Completed')
        ],
        default='identified'
    )

    requirement_ids = fields.Many2many(
        'risk.compliance.requirement'
    )