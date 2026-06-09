from odoo import models, fields


class RiskScorecard(models.Model):
    _name = 'risk.scorecard'
    _description = 'Risk Scorecard'

    name = fields.Char()

    period = fields.Char()

    risk_score = fields.Float()

    compliance_score = fields.Float()

    audit_score = fields.Float()

    resilience_score = fields.Float()

    overall_score = fields.Float(
        compute='_compute_score',
        store=True
    )

    def _compute_score(self):

        for rec in self:

            rec.overall_score = (
                rec.risk_score +
                rec.compliance_score +
                rec.audit_score +
                rec.resilience_score
            ) / 4