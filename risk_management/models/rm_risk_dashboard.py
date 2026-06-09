from odoo import models, fields, api


class RiskDashboard(models.Model):
    _name = 'risk.dashboard'
    _description = 'Executive Dashboard'

    name = fields.Char(
        required=True
    )

    report_date = fields.Date(
        default=fields.Date.today
    )

    total_risks = fields.Integer(
        compute='_compute_metrics'
    )

    critical_risks = fields.Integer(
        compute='_compute_metrics'
    )

    open_incidents = fields.Integer(
        compute='_compute_metrics'
    )

    open_findings = fields.Integer(
        compute='_compute_metrics'
    )

    compliance_rate = fields.Float(
        compute='_compute_metrics'
    )

    resilience_score = fields.Float(
        compute='_compute_metrics'
    )

    def _compute_metrics(self):

        Risk = self.env['risk.risk']
        Incident = self.env['risk.incident']
        Finding = self.env['risk.audit.finding']
        Compliance = self.env[
            'risk.compliance.assessment'
        ]

        for rec in self:

            rec.total_risks = Risk.search_count([])

            rec.critical_risks = Risk.search_count([
                ('current_risk_level', '=', 'critical')
            ])

            rec.open_incidents = Incident.search_count([
                ('status', '!=', 'closed')
            ])

            rec.open_findings = Finding.search_count([
                ('state', '!=', 'closed')
            ])

            assessments = Compliance.search([])

            if assessments:

                rec.compliance_rate = (
                    sum(
                        assessments.mapped(
                            'compliance_percentage'
                        )
                    )
                    /
                    len(assessments)
                )