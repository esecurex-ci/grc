from odoo import models, fields


class RiskMetricEngine(models.Model):
    _name = 'risk.metric.engine'
    _description = 'GRC Metric Engine'

    name = fields.Char(
        default='Metric Engine'
    )

    active = fields.Boolean(
        default=True
    )

    def action_calculate_grc_score(self):

        score = self.env[
            'risk.grc.score'
        ].create({

            'risk_score':
                self._calculate_risk_score(),

            'control_score':
                self._calculate_control_score(),

            'audit_score':
                self._calculate_audit_score(),

            'compliance_score':
                self._calculate_compliance_score(),

            'resilience_score':
                self._calculate_resilience_score(),

            'cyber_score':
                self._calculate_cyber_score()

        })

        return score

    def _calculate_risk_score(self):

        risks = self.env['risk.assessment'].search([])

        if not risks:
            return 100

        total = 0

        for risk in risks:
            score = max(
                0,
                100 - (
                        risk.residual_score * 4
                )
            )

            total += score

        return round(
            total / len(risks),
            2
        )

    def _calculate_control_score(self):
        controls = self.env[
            'risk.control'
        ].search([])
        if not controls:
            return 0

        return round(sum(controls.mapped('effectiveness')) / len(controls), 2)

    def _calculate_audit_score(self):

        findings = self.env[
            'risk.audit.finding'
        ].search([
            ('state', '!=', 'closed')
        ])

        total_findings = self.env[
            'risk.audit.finding'
        ].search_count([])

        if total_findings == 0:
            return 100

        return round(

            (
                    1 -
                    (
                            len(findings)
                            /
                            total_findings
                    )
            )
            * 100,

            2

        )

    def _calculate_compliance_score(self):

        assessments = self.env[
            'risk.compliance.assessment'
        ].search([])

        if not assessments:
            return 0

        return round(

            sum(
                assessments.mapped(
                    'compliance_percentage'
                )
            )
            /
            len(assessments),

            2

        )

    def _calculate_resilience_score(self):

        bcp_count = self.env[
            'risk.bcp.plan'
        ].search_count([])

        process_count = self.env[
            'risk.process'
        ].search_count([])

        if process_count == 0:
            return 0

        return round(

            (
                    bcp_count
                    /
                    process_count
            )
            * 100,

            2

        )

    def _calculate_cyber_score(self):

        cyber_incidents = self.env[
            'risk.incident'
        ].search_count([
            (
                'category_id.name',
                'ilike',
                'Cyber'
            )
        ])

        score = 100 - (
                cyber_incidents * 5
        )

        return max(
            score,
            0
        )

    def action_generate_history(self):

        latest_score = self.env[
            'risk.grc.score'
        ].search(
            [],
            order='assessment_date desc',
            limit=1
        )

        previous_history = self.env[
            'risk.grc.history'
        ].search(
            [],
            order='period_date desc',
            limit=1
        )

        history = self.env[
            'risk.grc.history'
        ].create({

            'name':
                latest_score.name,

            'period_date':
                latest_score.assessment_date,

            'grc_score_id':
                latest_score.id,

            'overall_score':
                latest_score.overall_score,

            'risk_score':
                latest_score.risk_score,

            'control_score':
                latest_score.control_score,

            'audit_score':
                latest_score.audit_score,

            'compliance_score':
                latest_score.compliance_score,

            'resilience_score':
                latest_score.resilience_score,

            'cyber_score':
                latest_score.cyber_score,

            'maturity_level':
                latest_score.maturity_level,

            'previous_history_id':
                previous_history.id
                if previous_history
                else False

        })

        return history

    def action_generate_dashboard_snapshot(self):

        latest_grc = self.env[
            'risk.grc.score'
        ].search(
            [],
            limit=1,
            order='assessment_date desc'
        )

        history = self.env[
            'risk.grc.history'
        ].search(
            [],
            limit=1,
            order='period_date desc'
        )

        snapshot = self.env[
            'risk.executive.dashboard.snapshot'
        ].create({

            'name':
                f"Dashboard {fields.Date.today()}",

            'snapshot_date':
                fields.Date.today(),

            'grc_score_id':
                latest_grc.id,

            'grc_history_id':
                history.id,

            'overall_score':
                latest_grc.overall_score,

            'risk_score':
                latest_grc.risk_score,

            'compliance_score':
                latest_grc.compliance_score,

            'audit_score':
                latest_grc.audit_score,

            'resilience_score':
                latest_grc.resilience_score,

            'cyber_score':
                latest_grc.cyber_score,

            'maturity_level':
                latest_grc.maturity_level,

        })

        return snapshot

