from odoo import models, fields


class RiskComplianceEvidence(models.Model):
    _name = 'risk.compliance.evidence'
    _description = 'Compliance Evidence'

    assessment_id = fields.Many2one(
        'risk.compliance.assessment',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        required=True
    )

    evidence_date = fields.Date()

    description = fields.Html()

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Documents'
    )