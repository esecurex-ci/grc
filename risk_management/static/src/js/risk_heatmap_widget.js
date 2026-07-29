/** @odoo-module **/

console.log("🔥 Fichier risk_heatmap_widget.js chargé !");

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

console.log("🔥 Imports OK !");

export class RiskHeatmapWidget extends Component {
    static template = "risk_management.RiskHeatmapWidgetTemplate";

    setup() {
        console.log("🔥 Setup RiskHeatmapWidget !");
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            matrix: this.initializeMatrix(),
            residualMatrix: this.initializeMatrix(),
            totalRisks: 0,
            criticalCount: 0,
            highCount: 0,
            mediumCount: 0,
            lowCount: 0,
            risks: [],
        });

        onWillStart(async () => {
            console.log("🔥 onWillStart !");
            await this.loadRisks();
        });
    }

    // ============================================================
    // INITIALISATION
    // ============================================================

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

    // ============================================================
    // CHARGEMENT DES DONNÉES
    // ============================================================

    async loadRisks() {
        console.log("🔥 loadRisks !");
        try {
            const data = await this.orm.searchRead(
                "risk.risk",
                [],
                [
                    "id", "name", "code", "inherent_level", "inherent_score",
                    "inherent_impact", "inherent_probability",
                    "residual_impact", "residual_probability", "residual_score", "residual_level",
                    "category_id", "state", "active", "create_date",
                    "control_ids", "control_effectiveness_level"
                ],
                { limit: 1000 }
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
        } finally {
            this.state.loading = false;
        }
    }

    // ============================================================
    // TRAITEMENT DES DONNÉES
    // ============================================================

    processData(data) {
        console.log("🔥 processData - Début du traitement des données");

        const matrix = this.initializeMatrix();
        const residualMatrix = this.initializeMatrix();

        let total = data.length;
        let critical = 0, high = 0, medium = 0, low = 0;
        let totalScore = 0;

        // Statistiques résiduelles
        let residualCritical = 0, residualHigh = 0, residualMedium = 0, residualLow = 0;

        data.forEach(risk => {
            // ---- Matrice Inhérente ----
            const impact = parseInt(risk.inherent_impact) || 1;
            const prob = parseInt(risk.inherent_probability) || 1;
            if (matrix[impact]) {
                matrix[impact][prob] = (matrix[impact][prob] || 0) + 1;
            }

            // ---- Matrice Résiduelle (basée sur inhérent + contrôle) ----
            const inherentLevel = risk.inherent_level || 'low';
            const controlLevel = risk.control_effectiveness_level || 'ineffective';

            // Calcul du niveau résiduel selon la matrice Excel
            const residualLevel = this._getResidualLevelFromMatrix(inherentLevel, controlLevel);

            // Déterminer la position dans la matrice 5x5
            const position = this._getMatrixPositionFromLevel(residualLevel);
            const residualImpact = position.impact;
            const residualProb = position.prob;

            if (residualMatrix[residualImpact]) {
                residualMatrix[residualImpact][residualProb] = (residualMatrix[residualImpact][residualProb] || 0) + 1;
            }

            // ---- Statistiques inhérentes ----
            if (inherentLevel === 'critical') critical++;
            else if (inherentLevel === 'high') high++;
            else if (inherentLevel === 'medium') medium++;
            else low++;

            // ---- Statistiques résiduelles ----
            if (residualLevel === 'critical') residualCritical++;
            else if (residualLevel === 'high') residualHigh++;
            else if (residualLevel === 'medium') residualMedium++;
            else if (residualLevel === 'low') residualLow++;

            totalScore += risk.inherent_score || 0;
        });

        // Mise à jour de l'état
        this.state.matrix = matrix;
        this.state.residualMatrix = residualMatrix;
        this.state.totalRisks = total;
        this.state.criticalCount = critical;
        this.state.highCount = high;
        this.state.mediumCount = medium;
        this.state.lowCount = low;
        this.state.avgScore = total > 0 ? (totalScore / total).toFixed(1) : 0;
        this.state.risks = data;

        // Données pour les graphiques
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

        console.log("🔥 Dashboard chargé !");
        console.log("🔥 Matrice inhérente :", this.state.matrix);
        console.log("🔥 Matrice résiduelle :", this.state.residualMatrix);
        console.log("🔥 Statistiques résiduelles :", {
            critical: residualCritical,
            high: residualHigh,
            medium: residualMedium,
            low: residualLow
        });
    }

    // ============================================================
    // MATRICE RÉSIDUELLE - LOGIQUE EXCEL
    // ============================================================

    _getResidualLevelFromMatrix(inherentLevel, controlLevel) {
        /**
         * Matrice d'évaluation du risque résiduel - Version Excel
         *
         * ┌──────────────────┬─────────────────────┬──────────────────┐
         * │ Niveau inhérent  │ Efficacité contrôles │ Niveau résiduel  │
         * ├──────────────────┼─────────────────────┼──────────────────┤
         * │ critical/high    │ ineffective          │ high             │
         * │ medium           │ ineffective          │ medium           │
         * │ low              │ ineffective          │ low              │
         * │ critical/high    │ partially_effective  │ high             │
         * │ medium           │ partially_effective  │ medium           │
         * │ low              │ partially_effective  │ low              │
         * │ critical/high    │ effective            │ medium           │
         * │ medium           │ effective            │ low              │
         * │ low              │ effective            │ low              │
         * └──────────────────┴─────────────────────┴──────────────────┘
         */

        // Normaliser le niveau inhérent
        let normInherent = inherentLevel;
        if (inherentLevel === 'critical') normInherent = 'high';

        // Si le contrôle est inefficace ou partiellement efficace
        if (controlLevel === 'ineffective' || controlLevel === 'partially_effective') {
            return normInherent;
        }

        // Si le contrôle est efficace
        if (controlLevel === 'effective') {
            if (normInherent === 'high') return 'medium';
            if (normInherent === 'medium') return 'low';
            return 'low'; // low reste low
        }

        return normInherent;
    }

    _getMatrixPositionFromLevel(level) {
        const mapping = {
            'critical': { impact: 5, prob: 5 },
            'high': { impact: 4, prob: 4 },
            'medium': { impact: 3, prob: 3 },
            'low': { impact: 2, prob: 2 },
        };
        return mapping[level] || { impact: 3, prob: 3 };
    }

    // ============================================================
    // COULEURS (ÉCHELLE EXCEL)
    // ============================================================

    getMatrixColor(score) {
        // Échelle Excel : Faible (1-5), Modéré (6-15), Élevé (16-25)
        if (score <= 5) return '#28a745';   // Vert - Faible
        if (score <= 15) return '#ffc107';  // Jaune - Modéré
        return '#dc3545';                   // Rouge - Élevé
    }

    getCellClass(impact, likelihood) {
        const score = impact * likelihood;
        if (score <= 5) return 'hm-green';
        if (score <= 15) return 'hm-yellow';
        return 'hm-red';
    }

    getLevelBadge(level) {
        const badges = {
            'critical': 'badge-danger',
            'high': 'badge-warning',
            'medium': 'badge-info',
            'low': 'badge-success',
        };
        return badges[level] || 'badge-secondary';
    }

    getLevelLabel(level) {
        const labels = {
            'critical': '🔴 Critique',
            'high': '🟠 Élevé',
            'medium': '🟡 Modéré',
            'low': '🟢 Faible',
        };
        return labels[level] || level;
    }

    getScoreColor(score) {
        if (score >= 16) return '#dc3545';  // Élevé
        if (score >= 6) return '#ffc107';   // Modéré
        return '#28a745';                   // Faible
    }

    // ============================================================
    // ACTIONS / NAVIGATION
    // ============================================================

    /**
     * ✅ CORRECTION PRINCIPALE : Les méthodes d'action utilisent
     * this.action qui est correctement injecté via useService
     */
    openRiskList(impact, likelihood) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `Risques (Impact: ${impact}, Probabilité: ${likelihood})`,
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["inherent_impact", "=", String(impact)],
                ["inherent_probability", "=", String(likelihood)]
            ],
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

    openCriticalRisks() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Risques critiques",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            domain: [["inherent_level", "=", "critical"]],
            target: "current",
        });
    }

    openRiskById(riskId) {
        if (!riskId) {
            console.warn('No risk ID provided');
            return;
        }

        try {
            this.action.doAction({
                type: "ir.actions.act_window",
                name: "Détail du risque",
                res_model: "risk.risk",
                views: [[false, "form"]],
                res_id: riskId,
                target: "current",
            });
        } catch (error) {
            console.error('Error opening risk:', error);
            // Fallback: ouvrir dans une nouvelle fenêtre
            window.open(`/web#model=risk.risk&id=${riskId}`, '_blank');
        }
    }

    // ============================================================
    // DONNÉES DE TEST
    // ============================================================

    loadTestData() {
        console.log("🔥 loadTestData !");
        const matrix = this.initializeMatrix();
        matrix[5][5] = 1;
        matrix[4][4] = 1;
        matrix[3][3] = 1;
        matrix[2][2] = 0;
        matrix[1][1] = 0;

        const residualMatrix = this.initializeMatrix();
        residualMatrix[4][4] = 1;
        residualMatrix[3][3] = 1;
        residualMatrix[2][2] = 1;

        this.state.matrix = matrix;
        this.state.residualMatrix = residualMatrix;
        this.state.totalRisks = 15;
        this.state.criticalCount = 4;
        this.state.highCount = 3;
        this.state.mediumCount = 5;
        this.state.lowCount = 3;
        this.state.avgScore = "15.7";
        this.state.risks = [];

        this.state.inherentData = [
            { label: 'Critiques', value: 4, color: '#dc3545' },
            { label: 'Élevés', value: 3, color: '#fd7e14' },
            { label: 'Moyens', value: 5, color: '#ffc107' },
            { label: 'Faibles', value: 3, color: '#28a745' },
        ];

        this.state.residualData = [
            { label: 'Critiques', value: 0, color: '#dc3545' },
            { label: 'Élevés', value: 1, color: '#fd7e14' },
            { label: 'Moyens', value: 3, color: '#ffc107' },
            { label: 'Faibles', value: 11, color: '#28a745' },
        ];
    }
}

console.log("🔥 RiskHeatmapWidget exporté avec succès !");

// Enregistrement du widget
RiskHeatmapWidget.template = "risk_management.RiskHeatmapWidgetTemplate";
registry.category("components").add("risk_management.RiskHeatmapWidget", RiskHeatmapWidget);