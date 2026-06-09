from odoo import models, fields


class RiskRegulatoryReport(models.Model):
    _name = 'risk.regulatory.report'
    _description = 'Regulatory Report'

    name = fields.Char(
        required=True
    )

    framework_id = fields.Many2one(
        'risk.compliance.framework'
    )

    report_date = fields.Date()

    description = fields.Html()

    attachment_id = fields.Many2one(
        'ir.attachment'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted')
        ],
        default='draft'
    )