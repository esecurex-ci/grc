from odoo import models, fields


class RiskComplianceScorecard(models.Model):
    _name = 'risk.compliance.scorecard'
    _description = 'Compliance Scorecard'

    name = fields.Char()

    assessment_date = fields.Date()

    overall_score = fields.Float()

    framework_id = fields.Many2one(
        'risk.compliance.framework'
    )

    comment = fields.Html()