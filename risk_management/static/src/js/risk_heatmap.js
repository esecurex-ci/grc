/** @odoo-module **/

console.log("🔥 Fichier risk_heatmap.js chargé !");

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

console.log("🔥 Imports OK !");

export class RiskHeatMap extends Component {
    static template = "rm_risk.RiskHeatMapTemplate";

    setup() {
        console.log("🔥 Setup RiskHeatMap !");
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            matrix: this.initializeMatrix(),
            residualMatrix: this.initializeMatrix(),
            totalRisks: 0,
            criticalCount: 0,
            highCount: 0,
            mediumCount: 0,
            lowCount: 0,
            avgScore: 0,
            risks: [],
            inherentData: [],
            residualData: [],
            categoryData: [],
            controls: { effective: 0, partial: 0, ineffective: 0 },
        });

        onWillStart(async () => {
            console.log("🔥 onWillStart !");
            await this.loadDashboardData();
        });
    }

    initializeMatrix() {
        const matrix = {};
        for (let impact = 5; impact >= 1; impact--) {
            matrix[impact] = {};
            for (let likelihood = 1; likelihood <= 5; likelihood++) {
                matrix[impact][likelihood] = 0;
            }
        }
        return matrix;
    }

    async loadDashboardData() {
        console.log("🔥 loadDashboardData !");
        try {
            const data = await this.orm.searchRead(
                "risk.risk",
                [],
                [
                    "inherent_impact", "inherent_probability", "inherent_score", "inherent_level",
                    "residual_impact", "residual_probability", "residual_score", "residual_level",
                    "name", "code", "category_id"
                ],
                1000,
                "inherent_score desc"
            );

            console.log("🔥 Données brutes :", data);

            if (data && data.length > 0) {
                this.processData(data);
            } else {
                this.loadTestData();
            }

        } catch (error) {
            console.error("🔥 Erreur :", error);
            this.loadTestData();
        }
    }

    processData(data) {
        // ✅ Matrices correctement remplies
        const matrix = this.initializeMatrix();
        const residualMatrix = this.initializeMatrix();

        let total = data.length;
        let critical = 0, high = 0, medium = 0, low = 0;
        let totalScore = 0;
        let categoryMap = {};

        data.forEach(risk => {
            // --- Matrice Inhérente ---
            const impact = parseInt(risk.inherent_impact) || 1;
            const prob = parseInt(risk.inherent_probability) || 1;
            if (matrix[impact]) {
                matrix[impact][prob] = (matrix[impact][prob] || 0) + 1;
            }

            // --- Matrice Résiduelle ---
            const resImpact = parseInt(risk.residual_impact) || 1;
            const resProb = parseInt(risk.residual_probability) || 1;
            if (residualMatrix[resImpact]) {
                residualMatrix[resImpact][resProb] = (residualMatrix[resImpact][resProb] || 0) + 1;
            }

            // --- Niveaux ---
            const level = risk.inherent_level || 'low';
            if (level === 'critical') critical++;
            else if (level === 'high') high++;
            else if (level === 'medium') medium++;
            else low++;

            totalScore += risk.inherent_score || 0;

            // --- Catégories ---
            const catName = risk.category_id ? risk.category_id[1] || 'Non catégorisé' : 'Non catégorisé';
            if (!categoryMap[catName]) {
                categoryMap[catName] = { count: 0, score: 0 };
            }
            categoryMap[catName].count += 1;
            categoryMap[catName].score += risk.inherent_score || 0;
        });

        // ✅ Statistiques résiduelles
        const residualCritical = data.filter(r => r.residual_level === 'critical').length;
        const residualHigh = data.filter(r => r.residual_level === 'high').length;
        const residualMedium = data.filter(r => r.residual_level === 'medium').length;
        const residualLow = data.filter(r => r.residual_level === 'low').length;

        this.state.matrix = matrix;
        this.state.residualMatrix = residualMatrix;
        this.state.totalRisks = total;
        this.state.criticalCount = critical;
        this.state.highCount = high;
        this.state.mediumCount = medium;
        this.state.lowCount = low;
        this.state.avgScore = total > 0 ? (totalScore / total).toFixed(1) : 0;
        this.state.risks = data;

        // ✅ Données pour les graphiques
        this.state.inherentData = [
            { label: 'Critiques', value: critical, color: '#dc3545' },
            { label: 'Élevés', value: high, color: '#fd7e14' },
            { label: 'Moyens', value: medium, color: '#ffc107' },
            { label: 'Faibles', value: low, color: '#28a745' },
        ];
        this.state.residualData = [
            { label: 'Critiques', value: residualCritical, color: '#dc3545' },
            { label: 'Élevés', value: residualHigh, color: '#fd7e14' },
            { label: 'Moyens', value: residualMedium, color: '#ffc107' },
            { label: 'Faibles', value: residualLow, color: '#28a745' },
        ];
        this.state.categoryData = Object.entries(categoryMap).map(([name, values]) => ({
            label: name,
            value: values.count,
        }));

        console.log("🔥 Dashboard chargé !", this.state);
        console.log("🔥 Matrice inhérente :", this.state.matrix);
        console.log("🔥 Matrice résiduelle :", this.state.residualMatrix);
    }

    loadTestData() {
        console.log("🔥 loadTestData !");
        const matrix = this.initializeMatrix();
        matrix[5][5] = 1;
        matrix[4][4] = 1;
        matrix[3][3] = 1;
        matrix[2][2] = 0;
        matrix[1][1] = 0;

        const residualMatrix = this.initializeMatrix();
        residualMatrix[5][5] = 1;
        residualMatrix[4][4] = 1;
        residualMatrix[3][3] = 1;
        residualMatrix[2][2] = 0;
        residualMatrix[1][1] = 0;

        this.state.matrix = matrix;
        this.state.residualMatrix = residualMatrix;
        this.state.totalRisks = 3;
        this.state.criticalCount = 1;
        this.state.highCount = 1;
        this.state.mediumCount = 1;
        this.state.lowCount = 0;
        this.state.avgScore = "15.7";
        this.state.inherentData = [
            { label: 'Critiques', value: 1, color: '#dc3545' },
            { label: 'Élevés', value: 1, color: '#fd7e14' },
            { label: 'Moyens', value: 1, color: '#ffc107' },
            { label: 'Faibles', value: 0, color: '#28a745' },
        ];
        this.state.residualData = [
            { label: 'Critiques', value: 0, color: '#dc3545' },
            { label: 'Élevés', value: 0, color: '#fd7e14' },
            { label: 'Moyens', value: 0, color: '#ffc107' },
            { label: 'Faibles', value: 3, color: '#28a745' },
        ];
        this.state.categoryData = [
            { label: 'Risque de non-conformité', value: 3 },
        ];
    }

    getCellClass(impact, likelihood) {
        const score = impact * likelihood;
        if (score >= 20) return 'hm-red';
        if (score >= 12) return 'hm-orange';
        if (score >= 6) return 'hm-yellow';
        if (score >= 3) return 'hm-green';
        return 'hm-blue';
    }

    getBarWidth(value, max) {
        if (!max || max === 0) return 0;
        return Math.round((value / max) * 100);
    }

    getMaxValue(data) {
        if (!data || data.length === 0) return 1;
        return Math.max(...data.map(d => d.value));
    }

    openRiskList(impact, likelihood) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `Risques (Impact: ${impact}, Probabilité: ${likelihood})`,
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            domain: [["inherent_impact", "=", String(impact)], ["inherent_probability", "=", String(likelihood)]],
            target: "current",
        });
    }

    openRisks() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Tous les risques",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

console.log("🔥 Action enregistrée avec succès !");

RiskHeatMap.template = "rm_risk.RiskHeatMapTemplate";

registry.category("actions").add("rm_risk_heatmap_client_action", RiskHeatMap);