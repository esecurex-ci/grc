from odoo import models, fields


class RiskCrisisRegulatoryReporting(models.Model):
    _name = 'risk.crisis.regulatory.reporting'
    _description = 'Crisis Regulatory Reporting'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True
    )

    regulator = fields.Selection(
        [
            ('cosumaf', 'COSUMAF'),
            ('amf_uemoa', 'AMF-UMOA'),
            ('bceao', 'BCEAO'),
            ('other', 'Other')
        ],
        required=True
    )

    report_date = fields.Date(
        default=fields.Date.today
    )

    subject = fields.Char()

    report_content = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('submitted', 'Submitted')
        ],
        default='draft'
    )