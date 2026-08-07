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
        this.notification = useService("notification");

        this.state = useState({
            loading: true,
            // Matrices Heatmap
            matrix: this.initializeMatrix(),
            residualMatrix: this.initializeMatrix(),
            // Statistiques globales
            totalRisks: 0,
            highCount: 0,
            mediumCount: 0,
            lowCount: 0,
            avgScore: 0,
            risks: [],
            inherentData: [],
            residualData: [],
            categoryData: [],
            controls: { effective: 0, partial: 0, ineffective: 0 },
            highInherentRisks: [],
            highResidualRisks: [],
            actions: {
                overdue: 0,
                in_progress: 0,
                completed: 0,
                not_started: 0,
            },
            // Listes d'IDs des actions correctives par statut affiché
            // (permettent au clic sur chaque case du bloc "Avancement des
            // Actions Correctives" d'ouvrir la liste EXACTEMENT filtrée,
            // au lieu de rouvrir toutes les actions sans distinction).
            actionIds: {
                overdue: [],
                in_progress: [],
                completed: [],
                not_started: [],
            },
            categoryEvolution: [],
            narratives: [],
            // Export
            exporting: false,
            exportingInherentMatrix: false,
            exportingResidualMatrix: false,
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
                    "assessment_ids", "last_assessment_date",
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

            // Statistiques RÉELLES des actions correctives (indépendantes
            // des risques : chargées séparément pour ne pas bloquer
            // l'affichage du reste du dashboard en cas d'échec).
            await this.loadActionsData();

        } catch (error) {
            console.error("🔥 Erreur :", error);
            this.loadTestData();
            await this.loadActionsData();
        } finally {
            this.state.loading = false;
        }
    }

    async loadActionsData() {
        console.log("🔥 loadActionsData !");
        try {
            const actionsData = await this.orm.searchRead(
                "risk.corrective.action",
                [],
                ["id", "state"],
                { limit: 5000 }
            );

            const ids = { overdue: [], in_progress: [], completed: [], not_started: [] };
            actionsData.forEach(a => {
                if (a.state === 'overdue') {
                    ids.overdue.push(a.id);
                } else if (a.state === 'in_progress' || a.state === 'review') {
                    ids.in_progress.push(a.id);
                } else if (a.state === 'done') {
                    ids.completed.push(a.id);
                } else if (a.state === 'draft') {
                    ids.not_started.push(a.id);
                }
                // 'cancelled' : volontairement exclu des 4 compteurs affichés
            });

            this.state.actionIds = ids;
            this.state.actions = {
                overdue: ids.overdue.length,
                in_progress: ids.in_progress.length,
                completed: ids.completed.length,
                not_started: ids.not_started.length,
            };
        } catch (error) {
            console.error("🔥 Erreur chargement actions correctives :", error);
            // On conserve les valeurs déjà en place (données de test ou zéros)
        }
    }

    processData(data) {
        console.log("🔥 processData - Début du traitement des données");

        // ============================================================
        // 1. INITIALISATION DES MATRICES
        // ============================================================
        const matrix = this.initializeMatrix();
        const residualMatrix = this.initializeMatrix();

        // ============================================================
        // 2. VARIABLES STATISTIQUES
        // ============================================================
        let total = data.length;
        let high = 0, medium = 0, low = 0;
        let residualHigh = 0, residualMedium = 0, residualLow = 0;
        let totalScore = 0;
        let categoryMap = {};
        let controlStats = { effective: 0, partially_effective: 0, ineffective: 0 };

        // ============================================================
        // 3. PARCOURS DES RISQUES
        // ============================================================
        data.forEach(risk => {
            // ---- 3.1 Matrice Inhérente ----
            const impact = parseInt(risk.inherent_impact) || 1;
            const prob = parseInt(risk.inherent_probability) || 1;
            if (matrix[impact]) {
                matrix[impact][prob] = (matrix[impact][prob] || 0) + 1;
            }

            // ---- 3.2 Matrice Résiduelle (NOUVELLE LOGIQUE) ----
            // Basée sur : Niveau inhérent + Niveau de contrôle
            const inherentLevel = risk.inherent_level || 'low';
            const controlLevel = risk.control_effectiveness_level || 'ineffective';

            // Calcul du niveau résiduel selon la matrice
            const residualLevel = this._getResidualLevelFromMatrix(inherentLevel, controlLevel);

            // Déterminer la position dans la matrice 5x5
            const position = this._getMatrixPositionFromLevel(residualLevel);
            const residualImpact = position.impact;
            const residualProb = position.prob;

            if (residualMatrix[residualImpact]) {
                residualMatrix[residualImpact][residualProb] = (residualMatrix[residualImpact][residualProb] || 0) + 1;
            }

            // ---- 3.3 Statistiques des niveaux inhérents ----
            if (inherentLevel === 'high') high++;
            else if (inherentLevel === 'medium') medium++;
            else low++;

            // ---- 3.4 Statistiques des niveaux résiduels ----
            if (residualLevel === 'high') residualHigh++;
            else if (residualLevel === 'medium') residualMedium++;
            else if (residualLevel === 'low') residualLow++;

            // ---- 3.5 Score total ----
            totalScore += risk.inherent_score || 0;

            // ---- 3.6 Catégories ----
            const catId = risk.category_id ? risk.category_id[0] : false;
            const catName = risk.category_id ? risk.category_id[1] || 'Non catégorisé' : 'Non catégorisé';
            if (!categoryMap[catName]) {
                categoryMap[catName] = { count: 0, score: 0, id: catId };
            }
            categoryMap[catName].count += 1;
            categoryMap[catName].score += risk.inherent_score || 0;

            // ---- 3.7 Statistiques des contrôles ----
            if (controlLevel === 'effective') controlStats.effective++;
            else if (controlLevel === 'partially_effective') controlStats.partially_effective++;
            else controlStats.ineffective++;
        });

        // ============================================================
        // 4. TOUS LES RISQUES INHÉRENTS ÉLEVÉS (sans limite)
        // ============================================================
        const activeRisks = data.filter(r => r.active !== false);
        const highInherentRisks = activeRisks
            .filter(r => r.inherent_level === 'high')
            .sort((a, b) => (b.inherent_score || 0) - (a.inherent_score || 0))
            .map(r => ({
                id: r.id,
                name: r.name,
                code: r.code || 'N/A',
                level: r.inherent_level,
                score: r.inherent_score || 0,
                category: r.category_id ? r.category_id[1] : 'Non catégorisé',
            }));

        // ============================================================
        // 5. TOP 5 RISQUES RÉSIDUELS ÉLEVÉS NÉCESSITANT UNE ACTION
        // (le résiduel n'a pas de score numérique : on trie par score
        // inhérent, en indicateur de sévérité de départ, à titre de
        // priorisation secondaire au sein du groupe "résiduel élevé")
        // ============================================================
        // ============================================================
        // 5. TOUS LES RISQUES RÉSIDUELS ÉLEVÉS NÉCESSITANT UNE ACTION
        // (le résiduel n'a pas de score numérique : le tri utilise le
        // score inhérent comme simple indicateur de priorisation)
        // ============================================================
        const highResidualRisks = activeRisks
            .filter(r => r.residual_level === 'high')
            .sort((a, b) => (b.inherent_score || 0) - (a.inherent_score || 0))
            .map((r, index) => ({
                id: r.id,
                name: r.name,
                code: r.code || 'N/A',
                level: r.residual_level,
                score: r.inherent_score || 0,
                rank: index + 1,
                category: r.category_id ? r.category_id[1] : 'Non catégorisé',
            }));

        // ============================================================
        // 6. ACTIONS CORRECTIVES (Données de test)
        // ============================================================
        const actions = {
            overdue: 0,
            in_progress: 3,
            completed: 2,
            not_started: 11,
        };

        // ============================================================
        // 7. ÉVOLUTION PAR CATÉGORIE
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
        // 8. NARRATIVES
        // ============================================================
        const narratives = this.generateNarratives(activeRisks);

        // ============================================================
        // 9. MISE À JOUR DE L'ÉTAT
        // ============================================================
        this.state.matrix = matrix;
        this.state.residualMatrix = residualMatrix;
        this.state.totalRisks = total;
        this.state.highCount = high;
        this.state.mediumCount = medium;
        this.state.lowCount = low;
        this.state.avgScore = total > 0 ? (totalScore / total).toFixed(1) : 0;
        this.state.risks = data;

        // Données pour les graphiques inhérents
        // (le champ "level" sert au clic : ouvre risk.risk filtré sur inherent_level)
        this.state.inherentData = [
            { label: 'Élevés', value: high, color: '#dc3545', level: 'high' },
            { label: 'Modérés', value: medium, color: '#ffc107', level: 'medium' },
            { label: 'Faibles', value: low, color: '#28a745', level: 'low' },
        ];

        // Données pour les graphiques résiduels (basés sur la nouvelle logique)
        // (le champ "level" sert au clic : ouvre risk.risk filtré sur residual_level)
        this.state.residualData = [
            { label: 'Élevés', value: residualHigh, color: '#dc3545', level: 'high' },
            { label: 'Modérés', value: residualMedium, color: '#ffc107', level: 'medium' },
            { label: 'Faibles', value: residualLow, color: '#28a745', level: 'low' },
        ];

        // Données par catégorie (id conservé pour permettre le clic -> liste filtrée)
        this.state.categoryData = Object.entries(categoryMap).map(([name, values]) => ({
            label: name,
            value: values.count,
            id: values.id,
        }));

        // Autres données
        this.state.highInherentRisks = highInherentRisks;
        this.state.highResidualRisks = highResidualRisks;
        this.state.actions = actions;
        this.state.categoryEvolution = categoryEvolution;
        this.state.narratives = narratives;
        this.state.controls = controlStats;

        console.log("🔥 Dashboard chargé !");
        console.log("🔥 Matrice inhérente :", this.state.matrix);
        console.log("🔥 Matrice résiduelle (basée sur inhérent + contrôle) :", this.state.residualMatrix);
        console.log("🔥 Statistiques résiduelles :", {
            high: residualHigh,
            medium: residualMedium,
            low: residualLow
        });
    }

    // ============================================================
    // MATRICE RÉSIDUELLE - NOUVELLE LOGIQUE
    // ============================================================
    _getResidualLevelFromMatrix(inherentLevel, controlLevel) {
        /**
         * Matrice d'évaluation du risque résiduel
         *
         * | Niveau inhérent | Efficacité des contrôles | Niveau résiduel |
         * |-----------------|--------------------------|-----------------|
         * | high            | ineffective              | high            |
         * | medium          | ineffective              | medium          |
         * | low             | ineffective              | low             |
         * | high            | partially_effective      | high            |
         * | medium          | partially_effective      | medium          |
         * | low             | partially_effective      | low             |
         * | high            | effective                | medium          |
         * | medium          | effective                | low             |
         * | low             | effective                | low             |
         */

        // Si le contrôle est inefficace ou partiellement efficace
        if (controlLevel === 'ineffective' || controlLevel === 'partially_effective') {
            return inherentLevel;
        }

        // Si le contrôle est efficace
        if (controlLevel === 'effective') {
            if (inherentLevel === 'high') return 'medium';
            if (inherentLevel === 'medium') return 'low';
            return 'low'; // low reste low
        }

        return inherentLevel;
    }

    _getMatrixPositionFromLevel(level) {
        /**
         * Retourne la position (impact, probabilité) dans la matrice 5x5
         * en fonction du niveau de risque
         */
        const mapping = {
            'high': { impact: 4, prob: 4 },
            'medium': { impact: 3, prob: 3 },
            'low': { impact: 2, prob: 2 },
        };
        return mapping[level] || { impact: 3, prob: 3 };
    }

    _getImpactFromLevel(level) {
        const mapping = {
            'high': 4,
            'medium': 3,
            'low': 2,
        };
        return mapping[level] || 3;
    }

    _getProbabilityFromLevel(level) {
        const mapping = {
            'high': 4,
            'medium': 3,
            'low': 2,
        };
        return mapping[level] || 3;
    }

    // ============================================================
    // GÉNÉRATION DES NARRATIVES
    // ============================================================
    generateNarratives(risks) {
        const narratives = [];

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

        const highRisks = risks.filter(r => r.inherent_level === 'high');
        if (highRisks.length > 0) {
            narratives.push({
                icon: '🔴',
                text: `${highRisks.length} risque(s) à niveau élevé nécessitent une attention immédiate.`
            });
        }

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
        // Simulation de la matrice résiduelle avec la nouvelle logique
        residualMatrix[4][4] = 1;
        residualMatrix[3][3] = 1;
        residualMatrix[2][2] = 1;

        this.state.matrix = matrix;
        this.state.residualMatrix = residualMatrix;
        this.state.totalRisks = 15;
        this.state.highCount = 7;
        this.state.mediumCount = 5;
        this.state.lowCount = 3;
        this.state.avgScore = "15.7";
        this.state.inherentData = [
            { label: 'Élevés', value: 7, color: '#dc3545', level: 'high' },
            { label: 'Modérés', value: 5, color: '#ffc107', level: 'medium' },
            { label: 'Faibles', value: 3, color: '#28a745', level: 'low' },
        ];
        this.state.residualData = [
            { label: 'Élevés', value: 0, color: '#dc3545', level: 'high' },
            { label: 'Modérés', value: 3, color: '#ffc107', level: 'medium' },
            { label: 'Faibles', value: 12, color: '#28a745', level: 'low' },
        ];
        this.state.categoryData = [
            { label: 'Risque de non-conformité', value: 3, id: false },
            { label: 'Risque opératoire', value: 8, id: false },
            { label: 'Risque stratégique', value: 2, id: false },
            { label: 'Risque financier', value: 2, id: false },
        ];

        this.state.highInherentRisks = [
            { id: 1, name: 'Non respect de la réglementation', code: 'RISK-00001', level: 'high', score: 20, category: 'Risque de non-conformité' },
            { id: 2, name: 'Impossibilité de vendre le titre', code: 'RISK-00002', level: 'high', score: 16, category: 'Risque opératoire' },
        ];

        this.state.highResidualRisks = [
            { id: 1, name: 'Non respect de la réglementation', code: 'RISK-00001', level: 'high', score: 20, rank: 1, category: 'Risque de non-conformité' },
            { id: 2, name: 'Impossibilité de vendre le titre', code: 'RISK-00002', level: 'high', score: 16, rank: 2, category: 'Risque opératoire' },
        ];

        this.state.actions = {
            overdue: 0,
            in_progress: 3,
            completed: 2,
            not_started: 11,
        };
        // Pas d'IDs réels disponibles en mode données de test : les cases
        // du bloc "Actions Correctives" restent alors non cliquables
        // (voir openActionsByIds, qui ne fait rien si la liste est vide).
        this.state.actionIds = {
            overdue: [],
            in_progress: [],
            completed: [],
            not_started: [],
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

        this.state.controls = {
            effective: 5,
            partially_effective: 3,
            ineffective: 2,
        };
    }

    // ============================================================
    // EXPORT EN IMAGE
    // ============================================================
    async exportMatrixToImage() {
        this.state.exporting = true;

        try {
            // Récupérer le conteneur du tableau de bord
            const container = document.querySelector('.o_risk_heatmap_container');
            if (!container) {
                throw new Error('Conteneur non trouvé');
            }

            // Vérifier si html2canvas est disponible
            if (typeof html2canvas === 'undefined') {
                // Charger html2canvas dynamiquement
                await this._loadHtml2Canvas();
            }

            // Capturer le conteneur en image
            const canvas = await html2canvas(container, {
                scale: 2, // Meilleure qualité
                useCORS: true,
                backgroundColor: '#ffffff',
                logging: false,
                allowTaint: true,
                width: container.scrollWidth,
                height: container.scrollHeight,
                windowWidth: container.scrollWidth,
                windowHeight: container.scrollHeight,
            });

            // Créer le lien de téléchargement
            const link = document.createElement('a');
            link.download = `matrices_risques_${new Date().toISOString().slice(0,10)}.png`;
            link.href = canvas.toDataURL('image/png');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.notification.add('✅ Matrices exportées en PNG avec succès !', { type: 'success' });

        } catch (error) {
            console.error('Erreur lors de l\'export PNG :', error);
            // Fallback : exporter en HTML
            this._exportAsHTML();
        } finally {
            this.state.exporting = false;
        }
    }

    _loadHtml2Canvas() {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js';
            script.onload = () => {
                console.log('html2canvas chargé !');
                resolve();
            };
            script.onerror = () => {
                reject(new Error('Impossible de charger html2canvas'));
            };
            document.head.appendChild(script);
        });
    }

    _exportAsHTML() {
        try {
            const html = this._generateExportHTML();
            const blob = new Blob([html], { type: 'text/html' });
            const link = document.createElement('a');
            link.download = `rapport_matrices_${new Date().toISOString().slice(0,10)}.html`;
            link.href = URL.createObjectURL(blob);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(link.href);

            this.notification.add('✅ Rapport HTML exporté !', { type: 'success' });
        } catch (error) {
            console.error('Erreur export HTML :', error);
            this.notification.add('❌ Erreur lors de l\'export', { type: 'danger' });
        }
    }

    _generateExportHTML() {
        const matrixData = this.state.matrix;
        const residualData = this.state.residualMatrix;

        let inherentRows = '';
        let residualRows = '';

        // Générer les lignes de la matrice inhérente
        for (let impact = 5; impact >= 1; impact--) {
            let cells = '';
            for (let prob = 1; prob <= 5; prob++) {
                const value = matrixData[impact] && matrixData[impact][prob] ? matrixData[impact][prob] : 0;
                const score = impact * prob;
                const color = this._getExportColor(score);
                cells += `<td style="border:1px solid #dee2e6;padding:8px;text-align:center;background:${color};color:white;font-weight:bold;width:50px;height:40px;font-size:14px;">${value}</td>`;
            }
            inherentRows += `<tr><td style="border:1px solid #dee2e6;padding:8px;text-align:center;background:#f5f5f5;font-weight:bold;width:50px;">${impact}</td>${cells}</tr>`;
        }

        // Générer les lignes de la matrice résiduelle
        for (let impact = 5; impact >= 1; impact--) {
            let cells = '';
            for (let prob = 1; prob <= 5; prob++) {
                const value = residualData[impact] && residualData[impact][prob] ? residualData[impact][prob] : 0;
                const score = impact * prob;
                const color = this._getExportColor(score);
                cells += `<td style="border:1px solid #dee2e6;padding:8px;text-align:center;background:${color};color:white;font-weight:bold;width:50px;height:40px;font-size:14px;">${value}</td>`;
            }
            residualRows += `<tr><td style="border:1px solid #dee2e6;padding:8px;text-align:center;background:#f5f5f5;font-weight:bold;width:50px;">${impact}</td>${cells}</tr>`;
        }

        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Matrices des Risques</title>
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                body { font-family: 'Segoe UI', Arial, sans-serif; padding: 30px; background: #f5f7fa; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 35px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                h1 { color: #1a237e; text-align: center; margin-bottom: 5px; font-size: 28px; }
                .subtitle { text-align: center; color: #6c757d; margin-bottom: 20px; font-size: 14px; border-bottom: 2px solid #e8eaf6; padding-bottom: 15px; }
                .risk-count { text-align: center; font-size: 18px; font-weight: bold; color: #1a237e; margin: 15px 0 25px; padding: 12px; background: #e8eaf6; border-radius: 8px; }
                .matrices { display: flex; gap: 40px; justify-content: center; flex-wrap: wrap; }
                .matrix-container { flex: 1; min-width: 320px; }
                .matrix-container h3 { text-align: center; color: #1a237e; margin-bottom: 15px; font-size: 18px; }
                table { border-collapse: collapse; margin: 0 auto; width: 100%; max-width: 350px; }
                th { background: #1a237e; color: white; padding: 10px; border: 1px solid #dee2e6; text-align: center; width: 50px; height: 35px; font-size: 13px; }
                .legend { display: flex; justify-content: center; gap: 20px; margin-top: 25px; flex-wrap: wrap; padding: 15px 20px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6; }
                .legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
                .legend-color { width: 24px; height: 24px; border-radius: 4px; border: 1px solid #dee2e6; }
                .footer { text-align: center; margin-top: 25px; font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; padding-top: 20px; }
                .matrix-label { font-weight: bold; color: #495057; }
                @media print {
                    body { background: white; padding: 10px; }
                    .container { box-shadow: none; border: 1px solid #ddd; }
                    .no-print { display: none; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Matrices des Risques</h1>
                <div class="subtitle">Généré le ${new Date().toLocaleDateString('fr-FR')} à ${new Date().toLocaleTimeString('fr-FR')}</div>
                <div class="risk-count">Total des risques : ${this.state.totalRisks}</div>
                
                <div class="matrices">
                    <div class="matrix-container">
                        <h3>🔥 Matrice Inhérente</h3>
                        <table>
                            <tr><th></th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th></tr>
                            ${inherentRows}
                        </table>
                    </div>
                    <div class="matrix-container">
                        <h3>🔥 Matrice Résiduelle</h3>
                        <table>
                            <tr><th></th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th></tr>
                            ${residualRows}
                        </table>
                    </div>
                </div>
                
                <div class="legend">
                    <span class="legend-item"><span class="legend-color" style="background:#dc3545;"></span> Élevé (16-25)</span>
                    <span class="legend-item"><span class="legend-color" style="background:#ffc107;"></span> Modéré (6-15)</span>
                    <span class="legend-item"><span class="legend-color" style="background:#28a745;"></span> Faible (1-5)</span>
                </div>
                
                <div class="footer">
                    Rapport généré automatiquement depuis le système de gestion des risques
                </div>
            </div>
        </body>
        </html>
        `;
    }

    _getExportColor(score) {
        if (score >= 16) return '#dc3545';  // Rouge - Élevé
        if (score >= 6) return '#ffc107';   // Jaune - Modéré
        return '#28a745';                   // Vert - Faible
    }

    async _exportDirectly() {
        try {
            // Récupérer le conteneur à exporter
            const container = document.querySelector('.o_risk_heatmap_container');
            if (!container) {
                throw new Error('Conteneur non trouvé');
            }

            // Utiliser html2canvas si disponible
            if (typeof html2canvas !== 'undefined') {
                const canvas = await html2canvas(container, {
                    scale: 2,
                    useCORS: true,
                    backgroundColor: '#ffffff',
                    logging: false,
                    allowTaint: true,
                });

                // Télécharger l'image
                const link = document.createElement('a');
                link.download = `matrices_risques_${new Date().toISOString().slice(0,10)}.png`;
                link.href = canvas.toDataURL('image/png');
                link.click();

                this.notification.add('✅ Matrices exportées avec succès !', { type: 'success' });
            } else {
                // Fallback : utiliser l'action Odoo
                await this._exportWithOdooAction();
            }
        } catch (error) {
            console.error('Erreur d\'export direct :', error);
            // Fallback
            await this._exportWithOdooAction();
        } finally {
            this.state.exporting = false;
        }
    }

    async _exportWithOdooAction() {
        try {
            // Créer un rapport HTML simple
            const html = this._generateExportHTML();

            // Télécharger le HTML en tant que fichier
            const blob = new Blob([html], { type: 'text/html' });
            const link = document.createElement('a');
            link.download = `rapport_matrices_${new Date().toISOString().slice(0,10)}.html`;
            link.href = URL.createObjectURL(blob);
            link.click();
            URL.revokeObjectURL(link.href);

            this.notification.add('✅ Rapport exporté avec succès !', { type: 'success' });
        } catch (error) {
            console.error('Erreur d\'export Odoo :', error);
            this.notification.add('❌ Erreur lors de l\'export', { type: 'danger' });
        }
    }

    // ============================================================
    // FONCTIONS UTILITAIRES
    // ============================================================
    getCellClass(impact, likelihood) {
        const score = impact * likelihood;
        if (score >= 16) return 'hm-red';
        if (score >= 6) return 'hm-yellow';
        return 'hm-green';
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
            'high': 'badge-danger',
            'medium': 'badge-warning',
            'low': 'badge-success',
        };
        return badges[level] || 'badge-secondary';
    }

    getLevelLabel(level) {
        const labels = {
            'high': '🔴 Élevé',
            'medium': '🟡 Modéré',
            'low': '🟢 Faible',
        };
        return labels[level] || level;
    }

    getScoreColor(score) {
        if (score >= 16) return '#dc3545';
        if (score >= 6) return '#ffc107';
        return '#28a745';
    }

    // ============================================================
    // ACTIONS / NAVIGATION
    // ------------------------------------------------------------
    // Toutes les méthodes appelées depuis un gestionnaire t-on-click
    // du template sont déclarées comme des propriétés de classe en
    // fonction fléchée (arrow function) : cela garantit que "this"
    // reste bien lié à l'instance du composant, y compris lorsque la
    // méthode est invoquée depuis une fonction fléchée écrite en ligne
    // dans le template (ex: t-on-click="() => this.openRiskById(x)").
    // ============================================================
    openRiskList = (impact, likelihood) => {
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

    openRisks = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Tous les risques",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openHighRisks = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Risques à niveau élevé",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            domain: [["inherent_level", "=", "high"]],
            target: "current",
        });
    }

    openRiskById = (riskId) => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Détail du risque",
            res_model: "risk.risk",
            views: [[false, "form"]],
            res_id: riskId,
            target: "current",
        });
    }

    openActions = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Actions correctives",
            res_model: "risk.corrective.action",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    /**
     * Ouvre la liste des actions correctives filtrée sur les IDs exacts
     * du bucket cliqué (En retard / En cours / Terminé / Non commencé),
     * calculés par loadActionsData() à partir du champ "state" réel de
     * risk.corrective.action — et non plus un simple clic générique sur
     * toute la grille qui rouvrait TOUTES les actions sans distinction.
     */
    openActionsByIds = (ids, title) => {
        if (!ids || !ids.length) {
            return;
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: title || "Actions correctives",
            res_model: "risk.corrective.action",
            views: [[false, "list"], [false, "form"]],
            domain: [["id", "in", ids]],
            target: "current",
        });
    }

    /**
     * Ouvre la liste des risques filtrée sur un niveau donné (Élevé /
     * Modéré / Faible), en précisant le champ concerné : "inherent_level"
     * pour les indicateurs/graphiques inhérents, "residual_level" pour
     * les indicateurs/graphiques résiduels.
     */
    openRiskLevelList = (field, level, label) => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: label || "Risques",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            domain: [[field, "=", level]],
            target: "current",
        });
    }

    /**
     * Ouvre la liste des risques d'une catégorie donnée (utilisé par le
     * graphique "Niveau de Risque par Catégorie"). categoryId peut être
     * absent (ex: données de test) : on retombe alors sur un filtre par
     * le nom de la catégorie, ou sur "sans catégorie" le cas échéant.
     */
    openCategoryRisks = (categoryId, categoryLabel) => {
        let domain;
        if (categoryId) {
            domain = [["category_id", "=", categoryId]];
        } else if (categoryLabel && categoryLabel !== "Non catégorisé") {
            domain = [["category_id.name", "=", categoryLabel]];
        } else {
            domain = [["category_id", "=", false]];
        }
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `Risques - ${categoryLabel}`,
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            domain,
            target: "current",
        });
    }

    /**
     * La matrice résiduelle positionne chaque risque à un emplacement
     * FIXE selon son niveau résiduel (voir _getMatrixPositionFromLevel) :
     * Élevé -> (4,4), Modéré -> (3,3), Faible -> (2,2). Une cellule de
     * cette matrice n'est donc cliquable que si elle correspond à l'une
     * de ces positions ; on ne peut pas réutiliser le domaine de
     * openRiskList (impact/probabilité inhérents) qui ne s'applique
     * qu'à la matrice inhérente.
     */
    getResidualCellLevel(impact, prob) {
        const mapping = { 4: { 4: "high" }, 3: { 3: "medium" }, 2: { 2: "low" } };
        return (mapping[impact] && mapping[impact][prob]) || null;
    }

    openResidualCellRisks = (impact, prob) => {
        const level = this.getResidualCellLevel(impact, prob);
        if (!level) {
            return;
        }
        this.openRiskLevelList("residual_level", level, `Risques - Niveau résiduel ${this.getLevelLabel(level)}`);
    }

    // ============================================================
    // EXPORT EN PDF
    // ============================================================
    exportMatrixToPDF() {
        this.state.exporting = true;

        try {
            const html = this._generateExportHTML();
            const printWindow = window.open('', '_blank', 'width=1000,height=800');
            if (printWindow) {
                printWindow.document.write(html);
                printWindow.document.close();
                printWindow.focus();
                printWindow.print();

                printWindow.onafterprint = () => {
                    printWindow.close();
                    this.notification.add('✅ PDF généré avec succès !', { type: 'success' });
                };
            } else {
                this.notification.add('⚠️ Veuillez autoriser les popups', { type: 'warning' });
            }
        } catch (error) {
            console.error('Erreur export PDF :', error);
            this.notification.add('❌ Erreur lors de l\'export PDF', { type: 'danger' });
        } finally {
            this.state.exporting = false;
        }
    }

    // ============================================================
    // EXPORT : TOUT LE DASHBOARD
    // ============================================================
    async exportFullDashboard() {
        this.state.exporting = true;

        try {
            const container = document.querySelector('.o_risk_heatmap_container');
            if (!container) {
                throw new Error('Conteneur non trouvé');
            }

            if (typeof html2canvas === 'undefined') {
                await this._loadHtml2Canvas();
            }

            const canvas = await html2canvas(container, {
                scale: 2,
                useCORS: true,
                backgroundColor: '#ffffff',
                logging: false,
                allowTaint: true,
                width: container.scrollWidth,
                height: container.scrollHeight,
                windowWidth: container.scrollWidth,
                windowHeight: container.scrollHeight,
            });

            const link = document.createElement('a');
            link.download = `dashboard_risques_${new Date().toISOString().slice(0,10)}.png`;
            link.href = canvas.toDataURL('image/png');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.notification.add('✅ Dashboard exporté avec succès !', { type: 'success' });

        } catch (error) {
            console.error('Erreur export dashboard :', error);
            this.notification.add('❌ Erreur lors de l\'export', { type: 'danger' });
        } finally {
            this.state.exporting = false;
        }
    }

    // ============================================================
    // EXPORT : UNE SEULE MATRICE (bouton dédié sur chaque carte)
    // ============================================================
    async exportSingleMatrix(elementId, filenamePrefix) {
        const flagKey = elementId === 'inherent-heatmap' ? 'exportingInherentMatrix' : 'exportingResidualMatrix';
        this.state[flagKey] = true;

        try {
            const element = document.querySelector(`#${elementId}`);
            if (!element) {
                throw new Error('Conteneur non trouvé');
            }

            if (typeof html2canvas === 'undefined') {
                await this._loadHtml2Canvas();
            }

            const canvas = await html2canvas(element, {
                scale: 2,
                useCORS: true,
                backgroundColor: '#ffffff',
                logging: false,
                allowTaint: true,
            });

            const link = document.createElement('a');
            link.download = `${filenamePrefix}_${new Date().toISOString().slice(0, 10)}.png`;
            link.href = canvas.toDataURL('image/png');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.notification.add('✅ Matrice exportée avec succès !', { type: 'success' });

        } catch (error) {
            console.error('Erreur export matrice unique :', error);
            this.notification.add('❌ Erreur lors de l\'export de la matrice', { type: 'danger' });
        } finally {
            this.state[flagKey] = false;
        }
    }

    // ============================================================
    // EXPORT : UNIQUEMENT LES MATRICES
    // ============================================================
    async exportMatricesOnly() {
        this.state.exporting = true;

        try {
            // Récupérer uniquement les conteneurs des matrices
            const inherentElement = document.querySelector('#inherent-heatmap');
            const residualElement = document.querySelector('#residual-heatmap');

            if (!inherentElement || !residualElement) {
                throw new Error('Conteneurs des matrices non trouvés');
            }

            if (typeof html2canvas === 'undefined') {
                await this._loadHtml2Canvas();
            }

            // Capturer les deux matrices séparément
            const inherentCanvas = await html2canvas(inherentElement, {
                scale: 2,
                useCORS: true,
                backgroundColor: '#ffffff',
                logging: false,
                allowTaint: true,
            });

            const residualCanvas = await html2canvas(residualElement, {
                scale: 2,
                useCORS: true,
                backgroundColor: '#ffffff',
                logging: false,
                allowTaint: true,
            });

            // Créer une image combinée (côte à côte)
            const combinedCanvas = document.createElement('canvas');
            const totalWidth = inherentCanvas.width + residualCanvas.width + 40; // 40px d'espacement
            const maxHeight = Math.max(inherentCanvas.height, residualCanvas.height);
            combinedCanvas.width = totalWidth;
            combinedCanvas.height = maxHeight + 100; // +100 pour le titre

            const ctx = combinedCanvas.getContext('2d');

            // Fond blanc
            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, combinedCanvas.width, combinedCanvas.height);

            // Titre
            ctx.fillStyle = '#1a237e';
            ctx.font = 'bold 24px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('📊 Matrices des Risques', combinedCanvas.width / 2, 45);

            // Sous-titre
            ctx.fillStyle = '#6c757d';
            ctx.font = '14px Arial';
            ctx.fillText(`Généré le ${new Date().toLocaleDateString('fr-FR')} à ${new Date().toLocaleTimeString('fr-FR')}`, combinedCanvas.width / 2, 70);

            // Coller les deux images
            ctx.drawImage(inherentCanvas, 20, 90);
            ctx.drawImage(residualCanvas, inherentCanvas.width + 40, 90);

            // Ajouter une légende en bas
            const legendY = Math.max(inherentCanvas.height, residualCanvas.height) + 110;
            ctx.textAlign = 'center';
            ctx.font = '12px Arial';
            ctx.fillStyle = '#495057';

            const legendItems = [
                { color: '#dc3545', label: 'Élevé' },
                { color: '#ffc107', label: 'Modéré' },
                { color: '#28a745', label: 'Faible' },
            ];

            const totalLegendWidth = legendItems.length * 120;
            let startX = (combinedCanvas.width - totalLegendWidth) / 2;

            legendItems.forEach(item => {
                ctx.fillStyle = item.color;
                ctx.fillRect(startX, legendY - 8, 16, 16);
                ctx.fillStyle = '#495057';
                ctx.textAlign = 'center';
                ctx.fillText(item.label, startX + 50, legendY + 5);
                startX += 120;
            });

            // Télécharger l'image combinée
            const link = document.createElement('a');
            link.download = `matrices_risques_${new Date().toISOString().slice(0,10)}.png`;
            link.href = combinedCanvas.toDataURL('image/png');
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            this.notification.add('✅ Matrices exportées avec succès !', { type: 'success' });

        } catch (error) {
            console.error('Erreur export matrices :', error);
            this.notification.add('❌ Erreur lors de l\'export des matrices', { type: 'danger' });
        } finally {
            this.state.exporting = false;
        }
    }

    // ============================================================
    // EXPORT : PDF (via impression)
    // ============================================================
    exportMatrixToPDF() {
        this.state.exporting = true;

        try {
            // Générer un HTML avec uniquement les matrices
            const html = this._generateMatricesOnlyHTML();
            const printWindow = window.open('', '_blank', 'width=1000,height=800');
            if (printWindow) {
                printWindow.document.write(html);
                printWindow.document.close();
                printWindow.focus();
                printWindow.print();

                printWindow.onafterprint = () => {
                    printWindow.close();
                    this.notification.add('✅ PDF généré avec succès !', { type: 'success' });
                };
            } else {
                this.notification.add('⚠️ Veuillez autoriser les popups', { type: 'warning' });
            }
        } catch (error) {
            console.error('Erreur export PDF :', error);
            this.notification.add('❌ Erreur lors de l\'export PDF', { type: 'danger' });
        } finally {
            this.state.exporting = false;
        }
    }

    // ============================================================
    // GÉNÉRER UN HTML UNIQUEMENT POUR LES MATRICES
    // ============================================================
    _generateMatricesOnlyHTML() {
        const matrixData = this.state.matrix;
        const residualData = this.state.residualMatrix;

        let inherentRows = '';
        let residualRows = '';

        // ---- Matrice Inhérente ----
        for (let impact = 5; impact >= 1; impact--) {
            let cells = '';
            for (let prob = 1; prob <= 5; prob++) {
                const value = matrixData[impact] && matrixData[impact][prob] ? matrixData[impact][prob] : 0;
                const score = impact * prob;
                const color = this._getExportColor(score);
                cells += `<td style="border:1px solid #dee2e6;padding:8px;text-align:center;background:${color};color:white;font-weight:bold;width:50px;height:40px;font-size:14px;">${value}</td>`;
            }
            inherentRows += `<tr><td style="border:1px solid #dee2e6;padding:8px;text-align:center;background:#f5f5f5;font-weight:bold;width:50px;">${impact}</td>${cells}</tr>`;
        }

        // ---- Matrice Résiduelle ----
        for (let impact = 5; impact >= 1; impact--) {
            let cells = '';
            for (let prob = 1; prob <= 5; prob++) {
                const value = residualData[impact] && residualData[impact][prob] ? residualData[impact][prob] : 0;
                const score = impact * prob;
                const color = this._getExportColor(score);
                cells += `<td style="border:1px solid #dee2e6;padding:8px;text-align:center;background:${color};color:white;font-weight:bold;width:50px;height:40px;font-size:14px;">${value}</td>`;
            }
            residualRows += `<tr><td style="border:1px solid #dee2e6;padding:8px;text-align:center;background:#f5f5f5;font-weight:bold;width:50px;">${impact}</td>${cells}</tr>`;
        }

        return `
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Matrices des Risques</title>
            <style>
                * { box-sizing: border-box; margin: 0; padding: 0; }
                body { font-family: 'Segoe UI', Arial, sans-serif; padding: 30px; background: #f5f7fa; }
                .container { max-width: 1000px; margin: 0 auto; background: white; padding: 35px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
                h1 { color: #1a237e; text-align: center; margin-bottom: 5px; font-size: 28px; }
                .subtitle { text-align: center; color: #6c757d; margin-bottom: 20px; font-size: 14px; border-bottom: 2px solid #e8eaf6; padding-bottom: 15px; }
                .risk-count { text-align: center; font-size: 18px; font-weight: bold; color: #1a237e; margin: 15px 0 25px; padding: 12px; background: #e8eaf6; border-radius: 8px; }
                .matrices { display: flex; gap: 40px; justify-content: center; flex-wrap: wrap; }
                .matrix-container { flex: 1; min-width: 320px; }
                .matrix-container h3 { text-align: center; color: #1a237e; margin-bottom: 15px; font-size: 18px; }
                table { border-collapse: collapse; margin: 0 auto; width: 100%; max-width: 350px; }
                th { background: #1a237e; color: white; padding: 10px; border: 1px solid #dee2e6; text-align: center; width: 50px; height: 35px; font-size: 13px; }
                .axis-label { font-size: 11px; font-weight: 600; color: #495057; text-align: center; }
                .legend { display: flex; justify-content: center; gap: 20px; margin-top: 25px; flex-wrap: wrap; padding: 15px 20px; background: #f8f9fa; border-radius: 8px; border: 1px solid #dee2e6; }
                .legend-item { display: flex; align-items: center; gap: 8px; font-size: 13px; }
                .legend-color { width: 24px; height: 24px; border-radius: 4px; border: 1px solid #dee2e6; }
                .footer { text-align: center; margin-top: 25px; font-size: 12px; color: #6c757d; border-top: 1px solid #dee2e6; padding-top: 20px; }
                .matrix-label { font-weight: bold; color: #495057; }
                @media print {
                    body { background: white; padding: 10px; }
                    .container { box-shadow: none; border: 1px solid #ddd; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📊 Matrices des Risques</h1>
                <div class="subtitle">Généré le ${new Date().toLocaleDateString('fr-FR')} à ${new Date().toLocaleTimeString('fr-FR')}</div>
                <div class="risk-count">Total des risques : ${this.state.totalRisks}</div>
                
                <div class="matrices">
                    <div class="matrix-container">
                        <h3>🔥 Matrice Inhérente</h3>
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;padding:0 5px;">
                            <span style="font-size:11px;font-weight:600;color:#495057;">Impact ↑</span>
                            <span style="font-size:11px;font-weight:600;color:#495057;">Probabilité →</span>
                        </div>
                        <table>
                            <tr><th></th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th></tr>
                            ${inherentRows}
                        </table>
                    </div>
                    <div class="matrix-container">
                        <h3>🔥 Matrice Résiduelle</h3>
                        <div style="display:flex;justify-content:space-between;margin-bottom:5px;padding:0 5px;">
                            <span style="font-size:11px;font-weight:600;color:#495057;">Niveau inhérent ↑</span>
                            <span style="font-size:11px;font-weight:600;color:#495057;">Niveau de contrôle →</span>
                        </div>
                        <table>
                            <tr><th></th><th>Ineff.</th><th>Partiel</th><th>Effic.</th><th>Très eff.</th><th>Optimal</th></tr>
                            ${residualRows}
                        </table>
                    </div>
                </div>
                
                <div class="legend">
                    <span class="legend-item"><span class="legend-color" style="background:#dc3545;"></span> Élevé (16-25)</span>
                    <span class="legend-item"><span class="legend-color" style="background:#ffc107;"></span> Modéré (6-15)</span>
                    <span class="legend-item"><span class="legend-color" style="background:#28a745;"></span> Faible (1-5)</span>
                </div>
                
                <div class="footer">
                    Rapport généré automatiquement depuis le système de gestion des risques
                </div>
            </div>
        </body>
        </html>
        `;
    }
}

console.log("🔥 Action enregistrée avec succès !");

RiskHeatMap.template = "rm_risk.RiskHeatMapTemplate";

registry.category("actions").add("rm_risk_heatmap_client_action", RiskHeatMap);
registry.category("components").add("rm_risk.RiskHeatMap", RiskHeatMap);