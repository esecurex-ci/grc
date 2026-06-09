from odoo import models, fields


class RiskComplianceMapping(models.Model):
    _name = 'risk.compliance.mapping'
    _description = 'Compliance Mapping'
    _rec_name = 'requirement_id'

    requirement_id = fields.Many2one(
        'risk.compliance.requirement',
        required=True,
        ondelete='cascade'
    )

    process_id = fields.Many2one(
        'risk.process'
    )

    risk_id = fields.Many2one(
        'risk.risk'
    )

    control_id = fields.Many2one(
        'risk.control'
    )

    organization_id = fields.Many2one(
        'risk.organization'
    )

    coverage_level = fields.Selection(
        [
            ('full', 'Full Coverage'),
            ('partial', 'Partial Coverage'),
            ('none', 'No Coverage')
        ],
        default='partial'
    )

    comment = fields.Html()