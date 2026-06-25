/** @odoo-module **/

console.log("🏛️ Fichier executive_dashboard_widget.js chargé !");

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

console.log("🏛️ Imports OK !");

export class ExecutiveDashboard extends Component {
    static template = "risk_management.executive_dashboard";

    setup() {
        console.log("🏛️ Setup ExecutiveDashboard !");
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            totalRisks: 0,
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
            avgScore: 0,
            postureStatus: 'Chargement...',
            matrix: this.initializeMatrix(),
            topRisks: [],
            overAppetite: [],
            categoryStats: {},
            actionStats: {
                not_started: 0,
                in_progress: 0,
                completed: 0,
                delayed: 0,
            },
            narratives: [],
            loading: true,
        });

        onWillStart(async () => {
            console.log("🏛️ onWillStart !");
            await this.loadDashboardData();
        });
    }

    initializeMatrix() {
        const matrix = {};
        for (let impact = 5; impact >= 1; impact--) {
            matrix[impact] = {};
            for (let likelihood = 1; likelihood <= 5; likelihood++) {
                matrix[impact][likelihood] = [];
            }
        }
        return matrix;
    }

    async loadDashboardData() {
        console.log("🏛️ loadDashboardData !");
        try {
            const data = await this.orm.searchRead(
                "risk.risk",
                [['active', '=', true]],
                [
                    "id", "name", "code",
                    "inherent_impact", "inherent_probability", "inherent_score", "inherent_level",
                    "residual_impact", "residual_probability", "residual_score", "residual_level",
                    "state", "category_id"
                ],
                1000,
                "inherent_score desc"
            );

            console.log("🏛️ Données brutes :", data);

            if (data && data.length > 0) {
                this.processData(data);
            } else {
                this.loadTestData();
            }

        } catch (error) {
            console.error("🏛️ Erreur :", error);
            this.loadTestData();
        } finally {
            this.state.loading = false;
        }
    }

    processData(data) {
        console.log("🏛️ Traitement des données :", data.length, "risques");

        const matrix = this.initializeMatrix();

        let total = data.length;
        let critical = 0, high = 0, medium = 0, low = 0;
        let totalScore = 0;
        let categoryMap = {};
        let overAppetite = [];
        let notStarted = 0, inProgress = 0, completed = 0, delayed = 0;

        data.forEach(risk => {
            // --- Matrice ---
            const impact = parseInt(risk.inherent_impact) || 1;
            const prob = parseInt(risk.inherent_probability) || 1;
            if (matrix[impact]) {
                matrix[impact][prob] = matrix[impact][prob] || [];
                matrix[impact][prob].push({
                    id: risk.id,
                    name: risk.name,
                    code: risk.code,
                    level: risk.inherent_level,
                    score: risk.inherent_score,
                });
            }

            // --- Niveaux ---
            const level = risk.inherent_level || 'low';
            if (level === 'critical') critical++;
            else if (level === 'high') high++;
            else if (level === 'medium') medium++;
            else low++;

            // --- Score total ---
            totalScore += risk.inherent_score || 0;

            // --- Catégories ---
            const catName = risk.category_id ? risk.category_id[1] || 'Non catégorisé' : 'Non catégorisé';
            categoryMap[catName] = (categoryMap[catName] || 0) + 1;

            // --- Hors appétit ---
            if (level === 'critical' || level === 'high') {
                overAppetite.push({
                    id: risk.id,
                    name: risk.name,
                    code: risk.code,
                    level: level,
                    score: risk.inherent_score,
                    state: risk.state,
                });
            }

            // --- Actions ---
            if (risk.state === 'draft') notStarted++;
            else if (risk.state === 'validated') inProgress++;
            else if (risk.state === 'obsolete') completed++;
        });

        // ✅ Top risques
        const topRisks = data.slice(0, 5).map(r => ({
            id: r.id,
            name: r.name,
            code: r.code,
            level: r.inherent_level,
            score: r.inherent_score,
            state: r.state,
        }));

        // ✅ Hors appétit (top 5)
        overAppetite = overAppetite.slice(0, 5);

        // ✅ Posture globale
        let posture;
        if (critical <= 2) posture = '✅ Dans appétit';
        else if (critical <= 4) posture = '⚠️ À surveiller';
        else posture = '🔴 Hors appétit';

        // ✅ Mise à jour de l'état
        this.state.matrix = matrix;
        this.state.totalRisks = total;
        this.state.critical = critical;
        this.state.high = high;
        this.state.medium = medium;
        this.state.low = low;
        this.state.avgScore = total > 0 ? (totalScore / total).toFixed(1) : 0;
        this.state.postureStatus = posture;
        this.state.overAppetite = overAppetite;
        this.state.topRisks = topRisks;
        this.state.categoryStats = categoryMap;
        this.state.actionStats = {
            not_started: notStarted,
            in_progress: inProgress,
            completed: completed,
            delayed: delayed,
        };
        this.state.narratives = [
            { icon: '🔺', text: 'Nouveau risque identifié : Risque de réputation' },
            { icon: '📈', text: 'Augmentation du risque Cyber (score: 16 → 20)' },
            { icon: '✅', text: 'Mise en place du plan de continuité fournisseur' },
            { icon: '⚠️', text: 'Retard dans le plan d\'action RGPD (report T4 2024)' },
        ];

        console.log("🏛️ Dashboard chargé !", this.state);
        console.log("🏛️ Matrice :", this.state.matrix);
    }

    loadTestData() {
        console.log("🏛️ loadTestData !");
        const matrix = this.initializeMatrix();
        matrix[5][5] = [{ id: 1, name: 'Test Critique', code: 'TEST-001', level: 'critical', score: 25 }];
        matrix[4][4] = [{ id: 2, name: 'Test Élevé', code: 'TEST-002', level: 'high', score: 16 }];
        matrix[3][3] = [{ id: 3, name: 'Test Moyen', code: 'TEST-003', level: 'medium', score: 9 }];

        this.state.matrix = matrix;
        this.state.totalRisks = 3;
        this.state.critical = 1;
        this.state.high = 1;
        this.state.medium = 1;
        this.state.low = 0;
        this.state.avgScore = "16.7";
        this.state.postureStatus = '⚠️ À surveiller';
        this.state.overAppetite = [
            { id: 1, name: 'Test Critique', code: 'TEST-001', level: 'critical', score: 25, state: 'draft' },
        ];
        this.state.topRisks = [
            { id: 1, name: 'Test Critique', code: 'TEST-001', level: 'critical', score: 25, state: 'draft' },
            { id: 2, name: 'Test Élevé', code: 'TEST-002', level: 'high', score: 16, state: 'validated' },
            { id: 3, name: 'Test Moyen', code: 'TEST-003', level: 'medium', score: 9, state: 'draft' },
        ];
        this.state.categoryStats = {
            'Risque de non-conformité': 3,
        };
        this.state.actionStats = {
            not_started: 2,
            in_progress: 1,
            completed: 0,
            delayed: 0,
        };
        this.state.narratives = [
            { icon: '🔺', text: 'Nouveau risque identifié : Risque de réputation' },
            { icon: '📈', text: 'Augmentation du risque Cyber' },
            { icon: '✅', text: 'Mise en place du plan de continuité' },
        ];
        this.state.loading = false;
    }

    // ============================================================
    // MÉTHODES UTILITAIRES POUR LE TEMPLATE
    // ============================================================

    getHeatmapColor(score) {
        if (score >= 20) return '#dc3545';
        if (score >= 12) return '#fd7e14';
        if (score >= 6) return '#f0ad4e';
        if (score >= 3) return '#28a745';
        return '#17a2b8';
    }

    getCellClass(impact, likelihood) {
        const score = impact * likelihood;
        if (score >= 20) return 'hm-red';
        if (score >= 12) return 'hm-orange';
        if (score >= 6) return 'hm-yellow';
        if (score >= 3) return 'hm-green';
        return 'hm-blue';
    }

    getCategoryMax() {
        const values = Object.values(this.state.categoryStats);
        return values.length > 0 ? Math.max(...values) : 1;
    }

    getActionTotal() {
        const stats = this.state.actionStats;
        return stats.not_started + stats.in_progress + stats.completed + stats.delayed || 1;
    }

    getCellCount(impact, likelihood) {
        const cell = this.state.matrix[impact]?.[likelihood] || [];
        return cell.length;
    }

    getBarWidth(value, max) {
        if (!max || max === 0) return 0;
        return Math.round((value / max) * 100);
    }

    getMaxValue(data) {
        if (!data || data.length === 0) return 1;
        return Math.max(...data.map(d => d.value));
    }

    // ============================================================
    // GESTION DES ÉVÉNEMENTS ET ACTIONS
    // ============================================================

    openRiskList(impact, likelihood) {
        const risks = this.state.matrix[impact]?.[likelihood] || [];
        const riskIds = risks.map(r => r.id);
        if (riskIds.length > 0) {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: `Risques (Impact: ${impact}, Probabilité: ${likelihood})`,
                res_model: "risk.risk",
                views: [[false, "list"], [false, "form"]],
                domain: [["id", "in", riskIds]],
                target: "current",
            });
        }
    }

    openAllRisks() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Tous les risques",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openOverAppetiteRisks() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Risques hors appétit",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            domain: [["inherent_level", "in", ["critical", "high"]]],
            target: "current",
        });
    }

    onMatrixCellClick(impact, likelihood) {
        this.openRiskList(impact, likelihood);
    }

    // Nouvelles méthodes pour les processus

    async loadProcessData() {
        console.log("🏛️ loadProcessData !");
        try {
            const processes = await this.orm.searchRead(
                "risk.process",
                [['active', '=', true]],
                ["id", "name", "code", "category", "macro_process_id", "owner_id", "count_risk", "risk_level"],
                1000
            );
            console.log("🏛️ Processus chargés :", processes);
            this.state.processes = processes;
        } catch (error) {
            console.error("🏛️ Erreur chargement processus :", error);
        }
    }
}


console.log("🏛️ ExecutiveDashboard exporté !");

ExecutiveDashboard.template = "risk_management.executive_dashboard";

registry.category("actions").add("executive_dashboard", ExecutiveDashboard);

console.log("🏛️ Action executive_dashboard enregistrée !");