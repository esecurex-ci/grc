from odoo import models, fields, api


class RiskComplianceScorecardLine(models.Model):
    _name = 'risk.compliance.scorecard.line'
    _description = 'Compliance Scorecard Line'
    _order = 'framework_id'

    scorecard_id = fields.Many2one(
        'risk.compliance.scorecard',
        required=True,
        ondelete='cascade'
    )

    framework_id = fields.Many2one(
        'risk.compliance.framework',
        required=True
    )

    requirement_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    mandatory_requirement_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    compliant_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    partially_compliant_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    non_compliant_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    obligation_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    overdue_obligation_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    action_plan_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    overdue_action_plan_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    evidence_count = fields.Integer(
        compute='_compute_kpis',
        store=True
    )

    compliance_rate = fields.Float(
        compute='_compute_kpis',
        store=True
    )

    risk_score = fields.Float(
        compute='_compute_kpis',
        store=True
    )

    compliance_level = fields.Selection(
        [
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('average', 'Average'),
            ('poor', 'Poor')
        ],
        compute='_compute_kpis',
        store=True
    )

    @api.depends(
        'framework_id',
        'scorecard_id.reference_date'
    )
    def _compute_kpis(self):

        Assessment = self.env[
            'risk.compliance.assessment'
        ]

        Requirement = self.env[
            'risk.compliance.requirement'
        ]

        Obligation = self.env[
            'risk.compliance.obligation'
        ]

        ActionPlan = self.env[
            'risk.compliance.action.plan'
        ]

        Evidence = self.env[
            'risk.compliance.evidence'
        ]

        for rec in self:

            requirements = Requirement.search([
                ('framework_id', '=', rec.framework_id.id)
            ])

            requirement_ids = requirements.ids

            rec.requirement_count = len(requirements)

            rec.mandatory_requirement_count = len(
                requirements.filtered(
                    lambda r: r.mandatory
                )
            )

            assessments = Assessment.search([
                ('requirement_id', 'in', requirement_ids)
            ])

            rec.compliant_count = len(
                assessments.filtered(
                    lambda a: a.compliance_level == 'compliant'
                )
            )

            rec.partially_compliant_count = len(
                assessments.filtered(
                    lambda a: a.compliance_level == 'partially'
                )
            )

            rec.non_compliant_count = len(
                assessments.filtered(
                    lambda a: a.compliance_level == 'non_compliant'
                )
            )

            total = (
                rec.compliant_count +
                rec.partially_compliant_count +
                rec.non_compliant_count
            )

            rec.compliance_rate = (
                rec.compliant_count * 100 / total
                if total else 0
            )

            obligations = Obligation.search([
                ('requirement_id', 'in', requirement_ids)
            ])

            rec.obligation_count = len(
                obligations
            )

            rec.overdue_obligation_count = len(
                obligations.filtered(
                    lambda o:
                    o.next_due_date and
                    o.next_due_date < fields.Date.today()
                )
            )

            action_plans = ActionPlan.search([
                (
                    'assessment_id.requirement_id',
                    'in',
                    requirement_ids
                )
            ])

            rec.action_plan_count = len(
                action_plans
            )

            rec.overdue_action_plan_count = len(
                action_plans.filtered(
                    lambda a:
                    a.target_date and
                    a.target_date < fields.Date.today() and
                    a.state != 'validated'
                )
            )

            rec.evidence_count = Evidence.search_count([
                (
                    'assessment_id.requirement_id',
                    'in',
                    requirement_ids
                )
            ])

            rec.risk_score = (
                rec.non_compliant_count * 10
            )

            if rec.compliance_rate >= 95:
                rec.compliance_level = 'excellent'

            elif rec.compliance_rate >= 85:
                rec.compliance_level = 'good'

            elif rec.compliance_rate >= 70:
                rec.compliance_level = 'average'

            else:
                rec.compliance_level = 'poor'