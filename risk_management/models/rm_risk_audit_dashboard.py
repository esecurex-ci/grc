from odoo import models, fields, api


class RiskAuditDashboard(models.Model):
    """Fournisseur d'indicateurs pour le tableau de bord OWL 'Audit'
    (missions, constats, recommandations, plans d'action).

    Suit le même principe que risk.continuity.dashboard.get_resilience_kpis :
    une SEULE méthode, source unique de vérité, appelée par le tableau de
    bord OWL — pas de modèle technique de stockage, ce dashboard n'a pas
    besoin d'écran pivot/graph séparé pour l'instant (contrairement à la
    Continuité), donc pas de champs 'compute' ni de vue formulaire ici,
    uniquement la méthode de calcul.
    """
    _name = 'risk.audit.dashboard'
    _description = 'Audit Dashboard (KPI provider)'

    name = fields.Char(default='Audit Dashboard')

    @api.model
    def get_audit_kpis(self):
        Plan = self.env['risk.audit.plan']
        Audit = self.env['risk.audit']
        Finding = self.env['risk.audit.finding']
        Recommendation = self.env['risk.audit.recommendation']
        ActionPlan = self.env['risk.audit.action.plan']

        today = fields.Date.today()

        # ------------------------------------------------------------
        # Plans d'audit
        # ------------------------------------------------------------
        all_plans = Plan.search([])
        plan_state_counts = {
            'draft': len(all_plans.filtered(lambda p: p.state == 'draft')),
            'approved': len(all_plans.filtered(lambda p: p.state == 'approved')),
            'closed': len(all_plans.filtered(lambda p: p.state == 'closed')),
        }

        # ------------------------------------------------------------
        # Missions d'audit
        # ------------------------------------------------------------
        all_audits = Audit.search([])
        audit_state_counts = {}
        audit_ids_by_state = {}
        for state in ('draft', 'planning', 'fieldwork', 'reporting', 'closed'):
            recs = all_audits.filtered(lambda a, s=state: a.state == s)
            audit_state_counts[state] = len(recs)
            audit_ids_by_state[state] = recs.ids

        overdue_audits = all_audits.filtered(
            lambda a: a.end_date and a.end_date < today and a.state != 'closed'
        )

        # ------------------------------------------------------------
        # Constats d'audit
        # ------------------------------------------------------------
        all_findings = Finding.search([])
        finding_severity_counts = {}
        finding_ids_by_severity = {}
        for sev in ('low', 'moderate', 'high', 'critical'):
            recs = all_findings.filtered(lambda f, s=sev: f.severity == s)
            finding_severity_counts[sev] = len(recs)
            finding_ids_by_severity[sev] = recs.ids

        finding_state_counts = {}
        finding_ids_by_state = {}
        for state in ('open', 'in_progress', 'closed'):
            recs = all_findings.filtered(lambda f, s=state: f.state == s)
            finding_state_counts[state] = len(recs)
            finding_ids_by_state[state] = recs.ids

        closed_findings = finding_state_counts.get('closed', 0)
        finding_closure_rate = (
            closed_findings * 100.0 / len(all_findings) if all_findings else 0.0
        )

        findings_without_recommendation = all_findings.filtered(
            lambda f: not f.recommendation_ids
        )

        major_open_findings = all_findings.filtered(
            lambda f: f.severity in ('high', 'critical') and f.state != 'closed'
        )

        # ------------------------------------------------------------
        # Recommandations
        # ------------------------------------------------------------
        all_recommendations = Recommendation.search([])
        recommendation_state_counts = {}
        recommendation_ids_by_state = {}
        for state in ('open', 'implemented', 'verified', 'closed'):
            recs = all_recommendations.filtered(lambda r, s=state: r.state == s)
            recommendation_state_counts[state] = len(recs)
            recommendation_ids_by_state[state] = recs.ids

        implemented_or_more = all_recommendations.filtered(
            lambda r: r.state in ('verified', 'closed')
        )
        recommendation_implementation_rate = (
            len(implemented_or_more) * 100.0 / len(all_recommendations)
            if all_recommendations else 0.0
        )

        overdue_recommendations = all_recommendations.filtered(
            lambda r: r.target_date and r.target_date < today
            and r.state not in ('verified', 'closed')
        )

        recommendations_without_action_plan = all_recommendations.filtered(
            lambda r: not r.action_plan_ids and r.state not in ('verified', 'closed')
        )

        # ------------------------------------------------------------
        # Plans d'action
        # ------------------------------------------------------------
        all_action_plans = ActionPlan.search([])
        action_plan_state_counts = {}
        action_plan_ids_by_state = {}
        for state in ('draft', 'in_progress', 'completed', 'validated', 'cancelled'):
            recs = all_action_plans.filtered(lambda a, s=state: a.state == s)
            action_plan_state_counts[state] = len(recs)
            action_plan_ids_by_state[state] = recs.ids

        overdue_action_plans = all_action_plans.filtered(
            lambda a: a.target_date and a.target_date < today
            and a.state not in ('completed', 'validated', 'cancelled')
        )

        return {
            # ---- Plans d'audit ----
            'total_plans': len(all_plans),
            'plan_state_counts': plan_state_counts,

            # ---- Missions ----
            'total_audits': len(all_audits),
            'audit_state_counts': audit_state_counts,
            'audit_ids_by_state': audit_ids_by_state,
            'overdue_audit_count': len(overdue_audits),
            'overdue_audit_ids': overdue_audits.ids,
            'closed_audit_count': audit_state_counts.get('closed', 0),

            # ---- Constats ----
            'total_findings': len(all_findings),
            'finding_severity_counts': finding_severity_counts,
            'finding_ids_by_severity': finding_ids_by_severity,
            'finding_state_counts': finding_state_counts,
            'finding_ids_by_state': finding_ids_by_state,
            'finding_closure_rate': round(finding_closure_rate, 2),
            'findings_without_recommendation_count': len(findings_without_recommendation),
            'findings_without_recommendation_ids': findings_without_recommendation.ids,
            'major_open_finding_ids': major_open_findings.ids,
            'major_open_finding_count': len(major_open_findings),

            # ---- Recommandations ----
            'total_recommendations': len(all_recommendations),
            'recommendation_state_counts': recommendation_state_counts,
            'recommendation_ids_by_state': recommendation_ids_by_state,
            'recommendation_implementation_rate': round(recommendation_implementation_rate, 2),
            'overdue_recommendation_count': len(overdue_recommendations),
            'overdue_recommendation_ids': overdue_recommendations.ids,
            'recommendations_without_action_plan_count': len(recommendations_without_action_plan),
            'recommendations_without_action_plan_ids': recommendations_without_action_plan.ids,

            # ---- Plans d'action ----
            'total_action_plans': len(all_action_plans),
            'action_plan_state_counts': action_plan_state_counts,
            'action_plan_ids_by_state': action_plan_ids_by_state,
            'overdue_action_plan_count': len(overdue_action_plans),
            'overdue_action_plan_ids': overdue_action_plans.ids,
        }
