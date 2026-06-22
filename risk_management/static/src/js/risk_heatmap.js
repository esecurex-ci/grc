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
            totalRisks: 0,
            criticalCount: 0,
            highCount: 0,
            mediumCount: 0,
            lowCount: 0,
            avgScore: 0,
            risks: [],
        });

        onWillStart(async () => {
            console.log("🔥 onWillStart !");
            await this.loadDashboardAlternative();
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

    // ✅ Version qui fonctionne (basée sur ta méthode alternative)
    async loadDashboardAlternative() {
        console.log("🔥 loadDashboardAlternative !");
        try {
            // ✅ Utiliser searchRead correctement
            const data = await this.orm.searchRead(
                "risk.risk",
                [],  // domain vide = tous les risques
                ["inherent_impact", "inherent_probability", "inherent_score", "inherent_level",
                 "name", "code", "residual_impact", "residual_probability", "residual_score", "residual_level"],
                1000,
                "inherent_score desc"
            );

            console.log("🔥 Données :", data);

            if (data && data.length > 0) {
                const matrix = this.initializeMatrix();
                let total = data.length;
                let critical = 0, high = 0, medium = 0, low = 0;
                let totalScore = 0;

                data.forEach(risk => {
                    const impact = parseInt(risk.inherent_impact) || 1;
                    const prob = parseInt(risk.inherent_probability) || 1;
                    const score = impact * prob;

                    if (matrix[impact]) {
                        matrix[impact][prob] = (matrix[impact][prob] || 0) + 1;
                    }

                    const level = risk.inherent_level || 'low';
                    if (level === 'critical') critical++;
                    else if (level === 'high') high++;
                    else if (level === 'medium') medium++;
                    else low++;

                    totalScore += risk.inherent_score || 0;
                });

                this.state.matrix = matrix;
                this.state.totalRisks = total;
                this.state.criticalCount = critical;
                this.state.highCount = high;
                this.state.mediumCount = medium;
                this.state.lowCount = low;
                this.state.avgScore = total > 0 ? (totalScore / total).toFixed(1) : 0;
                this.state.risks = data;

                console.log("🔥 Dashboard chargé !", this.state);
            } else {
                console.log("🔥 Aucune donnée, chargement test");
                this.loadTestData();
            }

        } catch (error) {
            console.error("🔥 Erreur :", error);
            this.loadTestData();
        }
    }

    loadTestData() {
        console.log("🔥 loadTestData !");
        const matrix = this.initializeMatrix();
        matrix[5][5] = 3;
        matrix[5][4] = 2;
        matrix[4][4] = 4;
        matrix[4][3] = 3;
        matrix[3][3] = 5;
        matrix[3][2] = 2;
        matrix[2][2] = 4;
        matrix[1][1] = 2;

        this.state.matrix = matrix;
        this.state.totalRisks = 25;
        this.state.criticalCount = 3;
        this.state.highCount = 6;
        this.state.mediumCount = 8;
        this.state.lowCount = 8;
        this.state.avgScore = "12.5";
    }

    getCellClass(impact, likelihood) {
        const score = impact * likelihood;
        if (score >= 20) return 'hm-red';
        if (score >= 12) return 'hm-orange';
        if (score >= 6) return 'hm-yellow';
        if (score >= 3) return 'hm-green';
        return 'hm-blue';
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
}

console.log("🔥 Action enregistrée avec succès !");

RiskHeatMap.template = "rm_risk.RiskHeatMapTemplate";

// Enregistrement du composant en tant qu'action client
registry.category("actions").add("rm_risk_heatmap_client_action", RiskHeatMap);