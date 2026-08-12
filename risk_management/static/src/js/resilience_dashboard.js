/** @odoo-module **/

import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ============================================================
// TABLEAU DE BORD RÉSILIENCE (PCA / PRA / BIA / EXERCICES)
// ============================================================
// Construit sur le même modèle que ProcessDashboard (KPI cards cliquables,
// donuts, barres, listes de creusement) pour donner à la partie Résilience
// la même présentation qu'aux tableaux de bord Processus et Risques, comme
// demandé. Les indicateurs de couverture PCA/PRA proviennent d'un seul appel
// serveur (risk.continuity.dashboard.get_resilience_kpis) qui fait le lien
// réel BCP<->processus / DRP<->actif, au lieu d'être recalculés ici avec une
// formule qui pourrait diverger de celle utilisée ailleurs (Cockpit,
// Executive Dashboard Snapshot) — voir le commentaire de cette méthode côté
// serveur pour le détail de ce qui a changé.
export class ResilienceDashboard extends Component {
    static template = "risk_management.resilience_dashboard";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,

            // KPI globaux (repris tels que renvoyés par get_resilience_kpis)
            kpis: {},

            // Répartition des activités critiques (BIA) par criticité
            activityDistribution: [],
            activityIdsByCriticality: {},

            // Répartition PCA / PRA / Exercices par statut (barres)
            bcpByState: [],
            bcpIdsByState: {},
            drpByState: [],
            drpIdsByState: {},
            exerciseByState: [],
            exerciseIdsByState: {},

            // Répartition des constats d'exercice par sévérité
            findingDistribution: [],
            findingIdsBySeverity: {},
            openMajorFindings: [],

            // Listes de creusement (le cœur de la correction du bug de
            // couverture : ces processus/actifs sont ceux réellement non
            // couverts, calculés côté serveur par une vraie jointure).
            uncoveredProcesses: [],
            uncoveredAssets: [],

            // ✅ Fraîcheur des plans (ISO 22301) et actions correctives
            // d'exercice (ISO 22398) — voir get_resilience_kpis côté serveur.
            stalePlans: [],
            openCorrectiveActions: [],

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
            const [kpis, bcps, drps, activities, exercises, findings, processes, assets] = await Promise.all([
                this.orm.call('risk.continuity.dashboard', 'get_resilience_kpis', []),
                this.orm.searchRead('risk.bcp.plan', [], ['id', 'name', 'process_id', 'state'], { limit: 500 }),
                this.orm.searchRead('risk.drp.plan', [], ['id', 'name', 'system_id', 'state'], { limit: 500 }),
                this.orm.searchRead('risk.bia.activity', [], ['id', 'name', 'bia_id', 'criticality'], { limit: 1000 }),
                this.orm.searchRead('risk.exercise', [], ['id', 'name', 'exercise_type', 'state', 'exercise_date'], { limit: 500 }),
                this.orm.searchRead('risk.exercise.finding', [], ['id', 'exercise_id', 'severity', 'recommendation', 'state', 'target_date', 'responsible_id'], { limit: 1000 }),
                this.orm.searchRead('risk.process', [], ['id', 'name', 'code'], { limit: 500 }),
                this.orm.searchRead('risk.asset', [], ['id', 'name', 'code', 'asset_type'], { limit: 500 }),
            ]);

            this.processDashboardData(kpis, bcps, drps, activities, exercises, findings, processes, assets);
        } catch (error) {
            console.error("Résilience — erreur de chargement :", error);
        } finally {
            this.state.loading = false;
        }
    }

    // ============================================================
    // TRAITEMENT DES DONNÉES
    // ============================================================
    processDashboardData(kpis, bcps, drps, activities, exercises, findings, processes, assets) {
        this.state.kpis = kpis;

        // ------------------------------------------------------
        // Activités critiques par criticité (donut)
        // ------------------------------------------------------
        const critLevels = [
            { key: 'critical', label: 'Critique', color: '#dc3545' },
            { key: 'high', label: 'Élevée', color: '#fd7e14' },
            { key: 'medium', label: 'Moyenne', color: '#ffc107' },
            { key: 'low', label: 'Faible', color: '#28a745' },
        ];
        const activityIdsByCriticality = {};
        critLevels.forEach(l => { activityIdsByCriticality[l.key] = []; });
        activities.forEach(a => {
            const key = a.criticality || 'low';
            if (!activityIdsByCriticality[key]) activityIdsByCriticality[key] = [];
            activityIdsByCriticality[key].push(a.id);
        });
        this.state.activityIdsByCriticality = activityIdsByCriticality;
        this.state.activityDistribution = critLevels.map(l => ({
            ...l,
            value: (activityIdsByCriticality[l.key] || []).length,
        }));

        // ------------------------------------------------------
        // PCA par statut
        // ------------------------------------------------------
        const bcpStates = [
            { key: 'draft', label: 'Brouillon', color: '#6c757d' },
            { key: 'approved', label: 'Approuvé', color: '#28a745' },
            { key: 'obsolete', label: 'Obsolète', color: '#dc3545' },
        ];
        const bcpIdsByState = { draft: [], approved: [], obsolete: [] };
        bcps.forEach(b => { (bcpIdsByState[b.state] || (bcpIdsByState[b.state] = [])).push(b.id); });
        this.state.bcpIdsByState = bcpIdsByState;
        this.state.bcpByState = bcpStates.map(s => ({ ...s, value: (bcpIdsByState[s.key] || []).length }));

        // ------------------------------------------------------
        // PRA par statut
        // ------------------------------------------------------
        const drpStates = [
            { key: 'draft', label: 'Brouillon', color: '#6c757d' },
            { key: 'approved', label: 'Approuvé', color: '#28a745' },
        ];
        const drpIdsByState = { draft: [], approved: [] };
        drps.forEach(d => { (drpIdsByState[d.state] || (drpIdsByState[d.state] = [])).push(d.id); });
        this.state.drpIdsByState = drpIdsByState;
        this.state.drpByState = drpStates.map(s => ({ ...s, value: (drpIdsByState[s.key] || []).length }));

        // ------------------------------------------------------
        // Exercices par statut
        // ------------------------------------------------------
        const exStates = [
            { key: 'planned', label: 'Planifié', color: '#1976d2' },
            { key: 'completed', label: 'Réalisé', color: '#28a745' },
        ];
        const exerciseIdsByState = { planned: [], completed: [] };
        exercises.forEach(e => { (exerciseIdsByState[e.state] || (exerciseIdsByState[e.state] = [])).push(e.id); });
        this.state.exerciseIdsByState = exerciseIdsByState;
        this.state.exerciseByState = exStates.map(s => ({ ...s, value: (exerciseIdsByState[s.key] || []).length }));

        // ------------------------------------------------------
        // Constats d'exercice par sévérité
        // ------------------------------------------------------
        const sevLevels = [
            { key: 'critical', label: 'Critique', color: '#dc3545' },
            { key: 'high', label: 'Élevée', color: '#fd7e14' },
            { key: 'medium', label: 'Moyenne', color: '#ffc107' },
            { key: 'low', label: 'Faible', color: '#28a745' },
        ];
        const findingIdsBySeverity = {};
        sevLevels.forEach(l => { findingIdsBySeverity[l.key] = []; });
        findings.forEach(f => {
            const key = f.severity || 'low';
            if (!findingIdsBySeverity[key]) findingIdsBySeverity[key] = [];
            findingIdsBySeverity[key].push(f.id);
        });
        this.state.findingIdsBySeverity = findingIdsBySeverity;
        this.state.findingDistribution = sevLevels.map(l => ({
            ...l,
            value: (findingIdsBySeverity[l.key] || []).length,
        }));

        const exerciseById = {};
        exercises.forEach(e => { exerciseById[e.id] = e; });
        this.state.openMajorFindings = findings
            .filter(f => f.severity === 'high' || f.severity === 'critical')
            .map(f => ({
                id: f.id,
                exerciseId: f.exercise_id ? f.exercise_id[0] : false,
                exerciseName: f.exercise_id ? f.exercise_id[1] : 'N/A',
                severity: f.severity,
                recommendation: this.stripHtml(f.recommendation),
            }));

        // ------------------------------------------------------
        // Listes de creusement — couverture réelle PCA / PRA
        // ------------------------------------------------------
        const processById = {};
        processes.forEach(p => { processById[p.id] = p; });
        this.state.uncoveredProcesses = (kpis.uncovered_process_ids || [])
            .map(id => processById[id])
            .filter(Boolean)
            .map(p => ({ id: p.id, name: p.name, code: p.code || 'N/A' }));

        const assetById = {};
        assets.forEach(a => { assetById[a.id] = a; });
        this.state.uncoveredAssets = (kpis.uncovered_asset_ids || [])
            .map(id => assetById[id])
            .filter(Boolean)
            .map(a => ({ id: a.id, name: a.name, code: a.code || 'N/A', assetType: a.asset_type || 'N/A' }));

        // ------------------------------------------------------
        // Fraîcheur des plans — PCA/PRA approuvés jamais testés ou testés
        // depuis plus de 12 mois (kpis.stale_bcp_ids / stale_drp_ids,
        // calculés côté serveur à partir du dernier exercice réalisé lié).
        // ------------------------------------------------------
        const bcpById = {};
        bcps.forEach(b => { bcpById[b.id] = b; });
        const drpById = {};
        drps.forEach(d => { drpById[d.id] = d; });

        const staleBcp = (kpis.stale_bcp_ids || [])
            .map(id => bcpById[id])
            .filter(Boolean)
            .map(b => ({ id: b.id, name: b.name, type: 'PCA', model: 'risk.bcp.plan' }));
        const staleDrp = (kpis.stale_drp_ids || [])
            .map(id => drpById[id])
            .filter(Boolean)
            .map(d => ({ id: d.id, name: d.name, type: 'PRA', model: 'risk.drp.plan' }));
        this.state.stalePlans = staleBcp.concat(staleDrp);

        // ------------------------------------------------------
        // Actions correctives d'exercice ouvertes (ISO 22398)
        // ------------------------------------------------------
        this.state.openCorrectiveActions = findings
            .filter(f => f.state && f.state !== 'closed')
            .map(f => ({
                id: f.id,
                exerciseId: f.exercise_id ? f.exercise_id[0] : false,
                exerciseName: f.exercise_id ? f.exercise_id[1] : 'N/A',
                severity: f.severity,
                state: f.state,
                targetDate: f.target_date || null,
                responsible: f.responsible_id ? f.responsible_id[1] : 'Non assigné',
                overdue: !!(f.target_date && f.target_date < new Date().toISOString().slice(0, 10)),
                recommendation: this.stripHtml(f.recommendation),
            }));

        // ------------------------------------------------------
        // Rapport narratif
        // ------------------------------------------------------
        this.state.narratives = this.generateNarratives(kpis);
    }

    stripHtml(html) {
        if (!html) return '';
        const div = document.createElement('div');
        div.innerHTML = html;
        return div.textContent || div.innerText || '';
    }

    generateNarratives(kpis) {
        const narratives = [];

        narratives.push({
            icon: kpis.bcp_coverage >= 80 ? '✅' : (kpis.bcp_coverage >= 50 ? '🟡' : '🔴'),
            text: `Couverture PCA : ${kpis.bcp_coverage}% des processus critiques (${kpis.covered_process_count}/${kpis.critical_process_count}) disposent d'un plan de continuité approuvé.`,
        });

        narratives.push({
            icon: kpis.drp_coverage >= 80 ? '✅' : (kpis.drp_coverage >= 50 ? '🟡' : '🔴'),
            text: `Couverture PRA : ${kpis.drp_coverage}% des actifs actifs (${kpis.covered_asset_count}/${kpis.total_assets}) disposent d'un plan de reprise approuvé.`,
        });

        if (this.state.uncoveredProcesses.length > 0) {
            narratives.push({
                icon: '⚠️',
                text: `${this.state.uncoveredProcesses.length} processus critique(s) n'ont encore aucun PCA approuvé.`,
            });
        }

        if (this.state.uncoveredAssets.length > 0) {
            narratives.push({
                icon: '⚠️',
                text: `${this.state.uncoveredAssets.length} actif(s) n'ont encore aucun PRA approuvé.`,
            });
        }

        narratives.push({
            icon: kpis.exercise_success_rate >= 80 ? '✅' : '🟡',
            text: `Taux de réussite des exercices réalisés : ${kpis.exercise_success_rate}% (sans constat Élevé/Critique).`,
        });

        if (this.state.openMajorFindings.length > 0) {
            narratives.push({
                icon: '🔴',
                text: `${this.state.openMajorFindings.length} constat(s) d'exercice Élevé(s)/Critique(s) à traiter.`,
            });
        }

        if (this.state.stalePlans.length > 0) {
            narratives.push({
                icon: '⏰',
                text: `${this.state.stalePlans.length} PCA/PRA approuvé(s) n'ont pas été testés depuis plus de 12 mois (ou jamais) — revue périodique attendue par ISO 22301.`,
            });
        }

        const overdueActions = this.state.openCorrectiveActions.filter(a => a.overdue);
        if (overdueActions.length > 0) {
            narratives.push({
                icon: '🔴',
                text: `${overdueActions.length} action(s) corrective(s) issue(s) d'exercice sont en retard par rapport à leur date cible.`,
            });
        } else if (this.state.openCorrectiveActions.length > 0) {
            narratives.push({
                icon: '🟡',
                text: `${this.state.openCorrectiveActions.length} action(s) corrective(s) issue(s) d'exercice restent ouvertes (aucune en retard).`,
            });
        }

        return narratives;
    }

    // ============================================================
    // RENDU D'UN DONUT (identique au tableau de bord Processus)
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

registry.category('actions').add('risk_management.resilience_dashboard', ResilienceDashboard);
