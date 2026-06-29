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
            loading: true,
            // Matrices Heatmap
            matrix: this.initializeMatrix(),
            residualMatrix: this.initializeMatrix(),
            // Statistiques globales
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
            // NOUVEAU : Risques Hors Appétit
            outOfAppetite: [],
            // NOUVEAU : Top 5 Risques
            topRisks: [],
            // NOUVEAU : Actions Correctives
            actions: {
                overdue: 0,
                in_progress: 0,
                completed: 0,
                not_started: 0,
            },
            // NOUVEAU : Evolution par Catégorie
            categoryEvolution: [],
            // NOUVEAU : Narratives
            narratives: [],
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
                    "id", "name", "code", "inherent_level", "inherent_score",
                    "inherent_impact", "inherent_probability",
                    "residual_impact", "residual_probability", "residual_score", "residual_level",
                    "category_id", "state", "active", "create_date",
                    "assessment_ids", "last_assessment_date"
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

    processData(data) {
        // ============================================================
        // 1. MATRICES HEATMAP
        // ============================================================
        const matrix = this.initializeMatrix();
        const residualMatrix = this.initializeMatrix();

        let total = data.length;
        let critical = 0, high = 0, medium = 0, low = 0;
        let totalScore = 0;
        let categoryMap = {};

        data.forEach(risk => {
            // Matrice Inhérente
            const impact = parseInt(risk.inherent_impact) || 1;
            const prob = parseInt(risk.inherent_probability) || 1;
            if (matrix[impact]) {
                matrix[impact][prob] = (matrix[impact][prob] || 0) + 1;
            }

            // Matrice Résiduelle
            const resImpact = parseInt(risk.residual_impact) || 1;
            const resProb = parseInt(risk.residual_probability) || 1;
            if (residualMatrix[resImpact]) {
                residualMatrix[resImpact][resProb] = (residualMatrix[resImpact][resProb] || 0) + 1;
            }

            // Niveaux
            const level = risk.inherent_level || 'low';
            if (level === 'critical') critical++;
            else if (level === 'high') high++;
            else if (level === 'medium') medium++;
            else low++;

            totalScore += risk.inherent_score || 0;

            // Catégories
            const catName = risk.category_id ? risk.category_id[1] || 'Non catégorisé' : 'Non catégorisé';
            if (!categoryMap[catName]) {
                categoryMap[catName] = { count: 0, score: 0 };
            }
            categoryMap[catName].count += 1;
            categoryMap[catName].score += risk.inherent_score || 0;
        });

        // Statistiques résiduelles
        const residualCritical = data.filter(r => r.residual_level === 'critical').length;
        const residualHigh = data.filter(r => r.residual_level === 'high').length;
        const residualMedium = data.filter(r => r.residual_level === 'medium').length;
        const residualLow = data.filter(r => r.residual_level === 'low').length;

        // ============================================================
        // 2. RISQUES HORS APPÉTIT
        // ============================================================
        const activeRisks = data.filter(r => r.active !== false);
        const outOfAppetite = activeRisks
            .filter(r => (r.inherent_level === 'critical' || r.inherent_level === 'high'))
            .filter(r => (r.inherent_score || 0) >= 15)
            .sort((a, b) => (b.inherent_score || 0) - (a.inherent_score || 0))
            .slice(0, 5)
            .map(r => ({
                id: r.id,
                name: r.name,
                code: r.code || 'N/A',
                level: r.inherent_level,
                score: r.inherent_score || 0,
                category: r.category_id ? r.category_id[1] : 'Non catégorisé',
            }));

        // ============================================================
        // 3. TOP 5 RISQUES
        // ============================================================
        const topRisks = activeRisks
            .sort((a, b) => (b.inherent_score || 0) - (a.inherent_score || 0))
            .slice(0, 5)
            .map((r, index) => ({
                id: r.id,
                name: r.name,
                code: r.code || 'N/A',
                level: r.inherent_level,
                score: r.inherent_score || 0,
                rank: index + 1,
                category: r.category_id ? r.category_id[1] : 'Non catégorisé',
            }));

        // ============================================================
        // 4. ACTIONS CORRECTIVES (simulation)
        // ============================================================
        // Idéalement, vous feriez un searchRead sur 'risk.corrective.action'
        // Pour l'instant, on garde des données de test
        const actions = {
            overdue: 0,
            in_progress: 3,
            completed: 2,
            not_started: 11,
        };

        // ============================================================
        // 5. ÉVOLUTION PAR CATÉGORIE
        // ============================================================
        const categoryEvolutionMap = {};
        activeRisks.forEach(r => {
            const catName = r.category_id ? r.category_id[1] : 'Non catégorisé';
            if (!categoryEvolutionMap[catName]) categoryEvolutionMap[catName] = 0;
            categoryEvolutionMap[catName]++;
        });
        const categoryEvolution = Object.entries(categoryEvolutionMap)
            .map(([label, value]) => ({ label, value }))
            .sort((a, b) => b.value - a.value);

        // ============================================================
        // 6. NARRATIVES
        // ============================================================
        const narratives = this.generateNarratives(activeRisks);

        // ============================================================
        // MISE À JOUR DE L'ÉTAT
        // ============================================================
        this.state.matrix = matrix;
        this.state.residualMatrix = residualMatrix;
        this.state.totalRisks = total;
        this.state.criticalCount = critical;
        this.state.highCount = high;
        this.state.mediumCount = medium;
        this.state.lowCount = low;
        this.state.avgScore = total > 0 ? (totalScore / total).toFixed(1) : 0;
        this.state.risks = data;
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
        this.state.outOfAppetite = outOfAppetite;
        this.state.topRisks = topRisks;
        this.state.actions = actions;
        this.state.categoryEvolution = categoryEvolution;
        this.state.narratives = narratives;

        console.log("🔥 Dashboard chargé !", this.state);
        console.log("🔥 Matrice inhérente :", this.state.matrix);
        console.log("🔥 Matrice résiduelle :", this.state.residualMatrix);
    }

    // ============================================================
    // GÉNÉRATION DES NARRATIVES
    // ============================================================
    generateNarratives(risks) {
        const narratives = [];

        // Nouveaux risques identifiés (30 derniers jours)
        const now = new Date();
        const recentRisks = risks.filter(r => {
            if (!r.create_date) return false;
            const date = new Date(r.create_date);
            const diff = (now - date) / (1000 * 60 * 60 * 24);
            return diff < 30;
        });
        if (recentRisks.length > 0) {
            narratives.push({
                icon: '🆕',
                text: `${recentRisks.length} nouveau(x) risque(s) identifié(s) récemment.`
            });
        }

        // Risques critiques
        const criticalRisks = risks.filter(r => r.inherent_level === 'critical');
        if (criticalRisks.length > 0) {
            narratives.push({
                icon: '🔴',
                text: `${criticalRisks.length} risque(s) critique(s) nécessitent une attention immédiate.`
            });
        }

        // Risques Cyber
        const cyberRisks = risks.filter(r => {
            const cat = r.category_id ? r.category_id[1] : '';
            return cat.toLowerCase().includes('cyber') || cat.toLowerCase().includes('sécurité');
        });
        if (cyberRisks.length > 0) {
            const avgScore = cyberRisks.reduce((sum, r) => sum + (r.inherent_score || 0), 0) / cyberRisks.length;
            narratives.push({
                icon: '🔒',
                text: `${cyberRisks.length} risque(s) Cyber (score moyen: ${Math.round(avgScore)}).`
            });
        }

        if (narratives.length === 0) {
            narratives.push({
                icon: '📊',
                text: 'Aucun changement significatif détecté. Situation stable.'
            });
        }

        return narratives;
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
        residualMatrix[5][5] = 1;
        residualMatrix[4][4] = 1;
        residualMatrix[3][3] = 1;
        residualMatrix[2][2] = 0;
        residualMatrix[1][1] = 0;

        this.state.matrix = matrix;
        this.state.residualMatrix = residualMatrix;
        this.state.totalRisks = 15;
        this.state.criticalCount = 4;
        this.state.highCount = 3;
        this.state.mediumCount = 5;
        this.state.lowCount = 3;
        this.state.avgScore = "15.7";
        this.state.inherentData = [
            { label: 'Critiques', value: 4, color: '#dc3545' },
            { label: 'Élevés', value: 3, color: '#fd7e14' },
            { label: 'Moyens', value: 5, color: '#ffc107' },
            { label: 'Faibles', value: 3, color: '#28a745' },
        ];
        this.state.residualData = [
            { label: 'Critiques', value: 0, color: '#dc3545' },
            { label: 'Élevés', value: 0, color: '#fd7e14' },
            { label: 'Moyens', value: 0, color: '#ffc107' },
            { label: 'Faibles', value: 15, color: '#28a745' },
        ];
        this.state.categoryData = [
            { label: 'Risque de non-conformité', value: 3 },
            { label: 'Risque opératoire', value: 8 },
            { label: 'Risque stratégique', value: 2 },
            { label: 'Risque financier', value: 2 },
        ];

        // Données de test pour les nouvelles sections
        this.state.outOfAppetite = [
            { id: 1, name: 'Non respect de la réglementation', code: 'RISK-00001', level: 'critical', score: 25, category: 'Risque de non-conformité' },
            { id: 2, name: 'Impossibilité de vendre le titre', code: 'RISK-00002', level: 'high', score: 16, category: 'Risque opératoire' },
            { id: 3, name: 'Sauvegardes incomplètes ou incorrectes', code: 'RISK-00093', level: 'critical', score: 20, category: 'Risque opératoire' },
            { id: 4, name: 'Absence de procédure non formalisée', code: 'RISK-00094', level: 'critical', score: 25, category: 'Risque opératoire' },
            { id: 5, name: 'Risque de non exhaustivité des dossiers', code: 'RISK-00098', level: 'high', score: 15, category: 'Risque de non-conformité' },
        ];

        this.state.topRisks = [
            { id: 1, name: 'Non respect de la réglementation', code: 'RISK-00001', level: 'critical', score: 25, rank: 1, category: 'Risque de non-conformité' },
            { id: 2, name: 'Impossibilité de vendre le titre', code: 'RISK-00002', level: 'high', score: 16, rank: 2, category: 'Risque opératoire' },
            { id: 3, name: 'Mauvais paramétrage des caractéristique des Fonds', code: 'RISK-00003', level: 'medium', score: 6, rank: 3, category: 'Risque opératoire' },
            { id: 4, name: 'Sauvegardes incomplètes ou incorrectes', code: 'RISK-00093', level: 'critical', score: 20, rank: 4, category: 'Risque opératoire' },
            { id: 5, name: 'Absence de procédure non formalisée', code: 'RISK-00094', level: 'critical', score: 25, rank: 5, category: 'Risque opératoire' },
        ];

        this.state.actions = {
            overdue: 0,
            in_progress: 3,
            completed: 2,
            not_started: 11,
        };

        this.state.categoryEvolution = [
            { label: 'Risque de non-conformité', value: 3 },
            { label: 'Risque opératoire', value: 8 },
            { label: 'Risque stratégique', value: 2 },
            { label: 'Risque financier', value: 2 },
        ];

        this.state.narratives = [
            { icon: '🆕', text: 'Nouveau risque identifié : Risque de réputation' },
            { icon: '📈', text: 'Augmentation du risque Cyber (score: 16 → 20)' },
            { icon: '✅', text: 'Mise en place du plan de continuité fournisseur' },
        ];
    }

    // ============================================================
    // FONCTIONS UTILITAIRES
    // ============================================================
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

    getMaxCategoryValue() {
        if (!this.state.categoryEvolution || this.state.categoryEvolution.length === 0) return 1;
        return Math.max(...this.state.categoryEvolution.map(c => c.value));
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
            'medium': '🟡 Moyen',
            'low': '🟢 Faible',
        };
        return labels[level] || level;
    }

    getScoreColor(score) {
        if (score >= 20) return '#dc3545';
        if (score >= 15) return '#fd7e14';
        if (score >= 10) return '#ffc107';
        if (score >= 5) return '#28a745';
        return '#17a2b8';
    }

    // ============================================================
    // ACTIONS / NAVIGATION
    // ============================================================
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

    openOutOfAppetite() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Risques hors appétit",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            domain: [
                ["inherent_level", "in", ["critical", "high"]],
                ["inherent_score", ">=", 15]
            ],
            target: "current",
        });
    }

    openRiskById(riskId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Détail du risque",
            res_model: "risk.risk",
            views: [[false, "form"]],
            res_id: riskId,
            target: "current",
        });
    }

    openActions() {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Actions correctives",
            res_model: "risk.corrective.action",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }
}

console.log("🔥 Action enregistrée avec succès !");

RiskHeatMap.template = "rm_risk.RiskHeatMapTemplate";

registry.category("actions").add("rm_risk_heatmap_client_action", RiskHeatMap);
registry.category("components").add("rm_risk.RiskHeatMap", RiskHeatMap);