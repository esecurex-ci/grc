from odoo import models, fields


class RiskComplianceFramework(models.Model):
    _name = 'risk.compliance.framework'
    _description = 'Compliance Framework'
    _inherit = ['mail.thread']

    name = fields.Char(
        required=True
    )

    code = fields.Char()

    version = fields.Char()

    publisher = fields.Char()

    publication_date = fields.Date()

    description = fields.Html()

    active = fields.Boolean(
        default=True
    )

    requirement_ids = fields.One2many(
        'risk.compliance.requirement',
        'framework_id'
    )