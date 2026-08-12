/** @odoo-module **/

import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ============================================================
// TABLEAU DE BORD AUDIT (PLAN D'AUDIT / MISSIONS / CONSTATS /
// RECOMMANDATIONS / PLANS D'ACTION)
// ============================================================
// Construit sur le même modèle que ProcessDashboard et ResilienceDashboard
// (KPI cards cliquables, donuts, barres, listes de creusement), pour donner
// à la partie Audit la même présentation qu'aux autres tableaux de bord du
// module. Tous les indicateurs proviennent d'un seul appel serveur
// (risk.audit.dashboard.get_audit_kpis), source unique de vérité, comme pour
// get_resilience_kpis côté Résilience.
export class AuditDashboard extends Component {
    static template = "risk_management.audit_dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,

            kpis: {},

            auditByState: [],
            auditIdsByState: {},

            findingBySeverity: [],
            findingIdsBySeverity: {},
            findingByState: [],
            findingIdsByState: {},

            recommendationByState: [],
            recommendationIdsByState: {},

            actionPlanByState: [],
            actionPlanIdsByState: {},

            overdueAudits: [],
            findingsWithoutRecommendation: [],
            recommendationsWithoutActionPlan: [],
            overdueRecommendations: [],
            majorOpenFindings: [],

            narratives: [],
        });

        onWillStart(async () => {
            await this.loadDashboardData();
        });
    }

    // ============================================================
    // CHARGEMENT DES DONNÉES
    // ============================================================
    async loadDashboardData() {
        try {
            const [kpis, audits, findings, recommendations, actionPlans] = await Promise.all([
                this.orm.call('risk.audit.dashboard', 'get_audit_kpis', []),
                this.orm.searchRead('risk.audit', [], ['id', 'name', 'title', 'state', 'end_date'], { limit: 1000 }),
                this.orm.searchRead('risk.audit.finding', [], ['id', 'name', 'title', 'audit_id', 'severity', 'state'], { limit: 2000 }),
                this.orm.searchRead('risk.audit.recommendation', [], ['id', 'finding_id', 'priority', 'target_date', 'state'], { limit: 2000 }),
                this.orm.searchRead('risk.audit.action.plan', [], ['id', 'name', 'recommendation_id', 'state', 'target_date'], { limit: 2000 }),
            ]);

            this.processDashboardData(kpis, audits, findings, recommendations, actionPlans);
        } catch (error) {
            console.error("Audit — erreur de chargement :", error);
        } finally {
            this.state.loading = false;
        }
    }

    // ============================================================
    // TRAITEMENT DES DONNÉES
    // ============================================================
    processDashboardData(kpis, audits, findings, recommendations, actionPlans) {
        this.state.kpis = kpis;

        const auditById = {};
        audits.forEach(a => { auditById[a.id] = a; });
        const findingById = {};
        findings.forEach(f => { findingById[f.id] = f; });
        const recommendationById = {};
        recommendations.forEach(r => { recommendationById[r.id] = r; });

        // ------------------------------------------------------
        // Missions par statut (barres)
        // ------------------------------------------------------
        const auditStates = [
            { key: 'draft', label: 'Brouillon', color: '#6c757d' },
            { key: 'planning', label: 'Planification', color: '#1976d2' },
            { key: 'fieldwork', label: 'Terrain', color: '#ffc107' },
            { key: 'reporting', label: 'Rédaction', color: '#fd7e14' },
            { key: 'closed', label: 'Clôturée', color: '#28a745' },
        ];
        this.state.auditIdsByState = kpis.audit_ids_by_state || {};
        this.state.auditByState = auditStates.map(s => ({
            ...s, value: (kpis.audit_state_counts || {})[s.key] || 0,
        }));

        // ------------------------------------------------------
        // Constats par sévérité (donut)
        // ------------------------------------------------------
        const sevLevels = [
            { key: 'critical', label: 'Critique', color: '#dc3545' },
            { key: 'high', label: 'Élevée', color: '#fd7e14' },
            { key: 'moderate', label: 'Modérée', color: '#ffc107' },
            { key: 'low', label: 'Faible', color: '#28a745' },
        ];
        this.state.findingIdsBySeverity = kpis.finding_ids_by_severity || {};
        this.state.findingBySeverity = sevLevels.map(l => ({
            ...l, value: (kpis.finding_severity_counts || {})[l.key] || 0,
        }));

        // ------------------------------------------------------
        // Constats par statut (donut secondaire)
        // ------------------------------------------------------
        const findingStates = [
            { key: 'open', label: 'Ouvert', color: '#dc3545' },
            { key: 'in_progress', label: 'En cours', color: '#ffc107' },
            { key: 'closed', label: 'Clôturé', color: '#28a745' },
        ];
        this.state.findingIdsByState = kpis.finding_ids_by_state || {};
        this.state.findingByState = findingStates.map(s => ({
            ...s, value: (kpis.finding_state_counts || {})[s.key] || 0,
        }));

        // ------------------------------------------------------
        // Recommandations par statut (barres)
        // ------------------------------------------------------
        const recStates = [
            { key: 'open', label: 'Ouverte', color: '#dc3545' },
            { key: 'implemented', label: 'Mise en œuvre', color: '#ffc107' },
            { key: 'verified', label: 'Vérifiée', color: '#1976d2' },
            { key: 'closed', label: 'Clôturée', color: '#28a745' },
        ];
        this.state.recommendationIdsByState = kpis.recommendation_ids_by_state || {};
        this.state.recommendationByState = recStates.map(s => ({
            ...s, value: (kpis.recommendation_state_counts || {})[s.key] || 0,
        }));

        // ------------------------------------------------------
        // Plans d'action par statut (barres)
        // ------------------------------------------------------
        const apStates = [
            { key: 'draft', label: 'Brouillon', color: '#6c757d' },
            { key: 'in_progress', label: 'En cours', color: '#ffc107' },
            { key: 'completed', label: 'Terminé', color: '#1976d2' },
            { key: 'validated', label: 'Validé', color: '#28a745' },
            { key: 'cancelled', label: 'Annulé', color: '#adb5bd' },
        ];
        this.state.actionPlanIdsByState = kpis.action_plan_ids_by_state || {};
        this.state.actionPlanByState = apStates.map(s => ({
            ...s, value: (kpis.action_plan_state_counts || {})[s.key] || 0,
        }));

        // ------------------------------------------------------
        // Listes de creusement
        // ------------------------------------------------------
        this.state.overdueAudits = (kpis.overdue_audit_ids || [])
            .map(id => auditById[id])
            .filter(Boolean)
            .map(a => ({ id: a.id, name: a.title || a.name, endDate: a.end_date }));

        this.state.findingsWithoutRecommendation = (kpis.findings_without_recommendation_ids || [])
            .map(id => findingById[id])
            .filter(Boolean)
            .map(f => ({ id: f.id, name: f.title || f.name, severity: f.severity }));

        this.state.recommendationsWithoutActionPlan = (kpis.recommendations_without_action_plan_ids || [])
            .map(id => recommendationById[id])
            .filter(Boolean)
            .map(r => ({
                id: r.id,
                findingName: r.finding_id ? r.finding_id[1] : 'N/A',
                priority: r.priority,
                targetDate: r.target_date || null,
            }));

        this.state.overdueRecommendations = (kpis.overdue_recommendation_ids || [])
            .map(id => recommendationById[id])
            .filter(Boolean)
            .map(r => ({
                id: r.id,
                findingName: r.finding_id ? r.finding_id[1] : 'N/A',
                priority: r.priority,
                targetDate: r.target_date || null,
            }));

        this.state.majorOpenFindings = (kpis.major_open_finding_ids || [])
            .map(id => findingById[id])
            .filter(Boolean)
            .map(f => ({
                id: f.id,
                name: f.title || f.name,
                severity: f.severity,
                auditName: f.audit_id ? f.audit_id[1] : 'N/A',
            }));

        // ------------------------------------------------------
        // Rapport narratif
        // ------------------------------------------------------
        this.state.narratives = this.generateNarratives(kpis);
    }

    generateNarratives(kpis) {
        const narratives = [];

        narratives.push({
            icon: '📋',
            text: `${kpis.total_audits || 0} mission(s) d'audit enregistrée(s), dont ${kpis.closed_audit_count || 0} clôturée(s).`,
        });

        if ((kpis.overdue_audit_count || 0) > 0) {
            narratives.push({
                icon: '🔴',
                text: `${kpis.overdue_audit_count} mission(s) ont dépassé leur date de fin prévue sans être clôturées.`,
            });
        }

        narratives.push({
            icon: kpis.finding_closure_rate >= 80 ? '✅' : (kpis.finding_closure_rate >= 50 ? '🟡' : '🔴'),
            text: `Taux de clôture des constats : ${kpis.finding_closure_rate}% (${kpis.finding_state_counts ? kpis.finding_state_counts.closed : 0}/${kpis.total_findings || 0}).`,
        });

        if ((kpis.findings_without_recommendation_count || 0) > 0) {
            narratives.push({
                icon: '⚠️',
                text: `${kpis.findings_without_recommendation_count} constat(s) n'ont encore aucune recommandation associée.`,
            });
        }

        narratives.push({
            icon: kpis.recommendation_implementation_rate >= 80 ? '✅' : (kpis.recommendation_implementation_rate >= 50 ? '🟡' : '🔴'),
            text: `Taux de mise en œuvre des recommandations (vérifiées ou clôturées) : ${kpis.recommendation_implementation_rate}%.`,
        });

        if ((kpis.overdue_recommendation_count || 0) > 0) {
            narratives.push({
                icon: '🔴',
                text: `${kpis.overdue_recommendation_count} recommandation(s) ont dépassé leur date cible sans être vérifiées/clôturées.`,
            });
        }

        if ((kpis.recommendations_without_action_plan_count || 0) > 0) {
            narratives.push({
                icon: '⚠️',
                text: `${kpis.recommendations_without_action_plan_count} recommandation(s) ouvertes n'ont encore aucun plan d'action associé.`,
            });
        }

        if ((kpis.overdue_action_plan_count || 0) > 0) {
            narratives.push({
                icon: '🔴',
                text: `${kpis.overdue_action_plan_count} plan(s) d'action sont en retard par rapport à leur échéance.`,
            });
        }

        if ((kpis.major_open_finding_count || 0) > 0) {
            narratives.push({
                icon: '🔴',
                text: `${kpis.major_open_finding_count} constat(s) Élevé(s)/Critique(s) restent ouverts.`,
            });
        }

        return narratives;
    }

    // ============================================================
    // RENDU D'UN DONUT (identique aux autres tableaux de bord)
    // ============================================================
    renderSingleDonut(item, total) {
        const circumference = 282.74;
        const percent = total > 0 ? item.value / total : 0;
        const offset = circumference * (1 - percent);

        const html = `
            <div class="donut-circle">
                <svg viewBox="0 0 120 120" width="120" height="120">
                    <circle cx="60" cy="60" r="45" fill="none" stroke="#f0f0f0" stroke-width="12"/>
                    <circle cx="60" cy="60" r="45" fill="none"
                            stroke="${item.color}" stroke-width="12"
                            stroke-linecap="round"
                            stroke-dasharray="${circumference}"
                            stroke-dashoffset="${offset}"
                            transform="rotate(-90 60 60)">
                        <animate attributeName="stroke-dashoffset"
                                 from="${circumference}" to="${offset}" dur="1s" fill="freeze"/>
                    </circle>
                    <text x="60" y="52" text-anchor="middle" font-size="20" font-weight="bold" fill="#1a237e">${item.value}</text>
                    <text x="60" y="72" text-anchor="middle" font-size="10" fill="#6c757d">${item.label}</text>
                </svg>
            </div>
            <div class="donut-label">
                <span class="donut-color" style="background:${item.color};"></span>
                ${item.label} (${item.value})
            </div>
        `;
        return markup(html);
    }

    getMax(list) {
        return Math.max(...list.map(i => i.value), 1);
    }

    // ============================================================
    // NAVIGATION
    // ============================================================
    openListByIds = (model, ids, title) => {
        if (!this.action) return;
        if (!ids || ids.length === 0) return;
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: title,
            res_model: model,
            views: [[false, 'list'], [false, 'form']],
            domain: [['id', 'in', ids]],
        });
    }

    openAll = (model, title, domain) => {
        if (!this.action) return;
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: title,
            res_model: model,
            views: [[false, 'list'], [false, 'form']],
            domain: domain || [],
        });
    }

    openRecord = (model, id, title) => {
        if (!this.action || !id) return;
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: title,
            res_model: model,
            views: [[false, 'form']],
            res_id: id,
        });
    }
}

registry.category('actions').add('risk_management.audit_dashboard', AuditDashboard);
