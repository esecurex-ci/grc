/** @odoo-module **/

console.log("📊 Fichier process_dashboard.js chargé !");

import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

console.log("📊 Imports OK !");

export class ProcessDashboard extends Component {
    static template = "risk_management.process_dashboard";

    setup() {
        console.log("📊 Setup ProcessDashboard !");
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            totalProcesses: 0,
            high: 0,
            medium: 0,
            low: 0,
            riskDistribution: [],
            highRiskProcesses: [],
            topProcesses: [],
            processesWithoutRisk: [],
            matrix: {},
            categoryStats: {},
            narratives: [],
            // Listes d'IDs de processus, utilisées pour la navigation au clic —
            // calculées à partir des mêmes données que l'affichage, ce qui
            // garantit que le clic ouvre exactement ce qui est montré à l'écran
            // (plutôt que de reconstruire un domaine serveur qui pourrait ne
            // pas correspondre exactement, ex. sur un champ d'échelle différent).
            residualHighProcessIds: [],
            residualMediumProcessIds: [],
            residualLowProcessIds: [],
            inherentHighProcessIds: [],
            noRiskProcessIds: [],
            categoryProcessIds: {},
            categoryLevelProcessIds: {}
        });

        onWillStart(async () => {
            console.log("📊 onWillStart !");
            await this.loadDashboardData();
        });
    }

    // ============================================================
    // CHARGEMENT DES DONNÉES - CORRIGÉ
    // ============================================================
    async loadDashboardData() {
        console.log("📊 loadDashboardData !");
        try {
            // ✅ CORRIGÉ : risk.process (champs corrects)
            const processes = await this.orm.searchRead(
                'risk.process',
                [],
                ['id', 'name', 'code', 'category', 'owner_id', 'risk_ids', 'risk_level', 'count_risk'],
                { limit: 100 }
            );

            console.log("📊 Processus bruts :", processes);

            // ✅ CORRIGÉ : risk.risk (champs corrects)
            const risks = await this.orm.searchRead(
                'risk.risk',
                [],
                ['id', 'process_id', 'inherent_level', 'residual_level', 'state', 'name', 'code'],
                { limit: 1000 }
            );

            console.log("📊 Risques bruts :", risks);

            if (processes && processes.length > 0) {
                this.processDashboardData(processes, risks);
            } else {
                this.loadTestData();
            }

        } catch (error) {
            console.error("📊 Erreur :", error);
            this.loadTestData();
        } finally {
            this.state.loading = false;
        }
    }

    // ============================================================
    // TRAITEMENT DES DONNÉES - CORRIGÉ
    // ============================================================
    processDashboardData(processes, risks) {
        // Créer un map des risques par processus
        const riskMap = {};
        risks.forEach(risk => {
            const processId = risk.process_id && risk.process_id[0];
            if (processId) {
                if (!riskMap[processId]) riskMap[processId] = [];
                riskMap[processId].push(risk);
            }
        });

        // Compter les risques par niveau pour chaque processus
        const processLevels = {};
        const categories = {};

        processes.forEach(process => {
            const processRisks = riskMap[process.id] || [];

            // ✅ Échelle à 3 niveaux : Élevé / Modéré / Faible — niveau INHÉRENT
            const highCount = processRisks.filter(r => r.inherent_level === 'high').length;
            const mediumCount = processRisks.filter(r => r.inherent_level === 'medium').length;
            const lowCount = processRisks.filter(r => r.inherent_level === 'low').length;

            // ✅ Même échelle, niveau RÉSIDUEL (exposition actuelle après contrôles)
            const residualHighCount = processRisks.filter(r => r.residual_level === 'high').length;
            const residualMediumCount = processRisks.filter(r => r.residual_level === 'medium').length;
            const residualLowCount = processRisks.filter(r => r.residual_level === 'low').length;

            // Déterminer le niveau global du processus, en inhérent ET en résiduel
            let level = 'low';
            if (highCount > 0) level = 'high';
            else if (mediumCount > 0) level = 'medium';

            let residualLevel = 'low';
            if (residualHighCount > 0) residualLevel = 'high';
            else if (residualMediumCount > 0) residualLevel = 'medium';

            // ✅ CORRIGÉ : utiliser le champ 'category' (Selection) directement
            const category = process.category || 'operational';
            const categoryLabel = this.formatCategory(category);

            processLevels[process.id] = {
                ...process,
                riskCount: processRisks.length,
                highCount,
                mediumCount,
                lowCount,
                level,
                residualHighCount,
                residualMediumCount,
                residualLowCount,
                residualLevel,
                categoryLabel
            };

            // Statistiques par catégorie (basées sur le niveau résiduel : c'est
            // l'exposition actuelle, après contrôles, qui pilote le dashboard)
            if (!categories[categoryLabel]) {
                categories[categoryLabel] = { high: 0, medium: 0, low: 0, total: 0 };
            }
            categories[categoryLabel][residualLevel]++;
            categories[categoryLabel].total++;
        });

        // ============================================================
        // 1. KPI CARDS (niveau résiduel : exposition actuelle après contrôles)
        // ============================================================
        this.state.totalProcesses = processes.length;
        this.state.high = Object.values(processLevels).filter(p => p.residualLevel === 'high').length;
        this.state.medium = Object.values(processLevels).filter(p => p.residualLevel === 'medium').length;
        this.state.low = Object.values(processLevels).filter(p => p.residualLevel === 'low').length;

        // ============================================================
        // 1bis. LISTES D'IDS — pour que chaque indicateur, une fois cliqué,
        // ouvre exactement les sous processus qu'il représente à l'écran.
        // ============================================================
        const allProcessValues = Object.values(processLevels);
        this.state.residualHighProcessIds = allProcessValues.filter(p => p.residualLevel === 'high').map(p => p.id);
        this.state.residualMediumProcessIds = allProcessValues.filter(p => p.residualLevel === 'medium').map(p => p.id);
        this.state.residualLowProcessIds = allProcessValues.filter(p => p.residualLevel === 'low').map(p => p.id);
        this.state.inherentHighProcessIds = allProcessValues.filter(p => p.level === 'high').map(p => p.id);
        this.state.noRiskProcessIds = allProcessValues.filter(p => p.riskCount === 0).map(p => p.id);

        // Par catégorie (pour les barres "Répartition par Macro-Processus")
        const categoryProcessIds = {};
        // Par catégorie x niveau résiduel (pour les cellules de la matrice)
        const categoryLevelProcessIds = {};
        allProcessValues.forEach(p => {
            if (!categoryProcessIds[p.categoryLabel]) categoryProcessIds[p.categoryLabel] = [];
            categoryProcessIds[p.categoryLabel].push(p.id);

            if (!categoryLevelProcessIds[p.categoryLabel]) {
                categoryLevelProcessIds[p.categoryLabel] = { high: [], medium: [], low: [] };
            }
            categoryLevelProcessIds[p.categoryLabel][p.residualLevel].push(p.id);
        });
        this.state.categoryProcessIds = categoryProcessIds;
        this.state.categoryLevelProcessIds = categoryLevelProcessIds;

        // ============================================================
        // 2. RISK DISTRIBUTION (pour les Donuts) - niveau résiduel
        // ============================================================
        this.state.riskDistribution = [
            { key: 'high', label: 'Élevé', value: this.state.high, color: '#dc3545' },
            { key: 'medium', label: 'Modéré', value: this.state.medium, color: '#ffc107' },
            { key: 'low', label: 'Faible', value: this.state.low, color: '#28a745' }
        ];

        // ============================================================
        // 3. SOUS PROCESSUS À RISQUE INHÉRENT ÉLEVÉ — pas de limite,
        //    le titre du panneau n'annonce aucun nombre maximum.
        // ============================================================
        this.state.highRiskProcesses = Object.values(processLevels)
            .filter(p => p.level === 'high')
            .map(p => ({
                id: p.id,
                name: p.name,
                code: p.code || 'N/A',
                count: p.riskCount,
                owner: p.owner_id ? p.owner_id[1] : 'Non assigné'
            }));

        // ============================================================
        // 4. SOUS PROCESSUS À RISQUE RÉSIDUEL ÉLEVÉ — filtré sur le
        //    niveau résiduel (et non plus un simple "top 5 par volume"),
        //    sans limite non plus.
        // ============================================================
        this.state.topProcesses = Object.values(processLevels)
            .filter(p => p.residualLevel === 'high')
            .sort((a, b) => b.riskCount - a.riskCount)
            .map(p => ({
                id: p.id,
                name: p.name,
                code: p.code || 'N/A',
                count: p.riskCount,
                level: p.residualLevel,
                owner: p.owner_id ? p.owner_id[1] : 'Non assigné'
            }));

        // ============================================================
        // 5. MATRICE PAR CATÉGORIE
        // ============================================================
        this.state.matrix = categories;

        // ============================================================
        // 6. STATISTIQUES PAR CATÉGORIE
        // ============================================================
        this.state.categoryStats = {};
        Object.keys(categories).forEach(cat => {
            this.state.categoryStats[cat] = categories[cat].total;
        });

        // ============================================================
        // 7. PROCESSUS SANS RISQUE
        // ============================================================
        this.state.processesWithoutRisk = Object.values(processLevels)
            .filter(p => p.riskCount === 0)
            .map(p => ({
                id: p.id,
                name: p.name,
                code: p.code || 'N/A',
                category: p.categoryLabel || 'Non classé'
            }));

        // ============================================================
        // 8. RAPPORT NARRATIF
        // ============================================================
        this.state.narratives = this.generateNarratives();

        console.log("📊 Dashboard chargé !", this.state);
    }

    // ============================================================
    // GÉNÉRATION DU RAPPORT NARRATIF
    // ============================================================
    generateNarratives() {
        const narratives = [];

        if (this.state.high > 0) {
            narratives.push({
                icon: '🔴',
                text: `${this.state.high} sous processus présentent un niveau de risque résiduel Élevé : attention prioritaire requise.`
            });
        } else {
            narratives.push({
                icon: '✅',
                text: 'Aucun sous processus à risque résiduel Élevé.'
            });
        }

        if (this.state.medium > 0) {
            narratives.push({
                icon: '🟡',
                text: `${this.state.medium} sous processus présentent un niveau de risque résiduel Modéré à surveiller.`
            });
        }

        if (this.state.low > 0) {
            narratives.push({
                icon: '🟢',
                text: `${this.state.low} sous processus présentent un niveau de risque résiduel Faible, sous contrôle.`
            });
        }

        if (this.state.processesWithoutRisk.length > 0) {
            narratives.push({
                icon: '📋',
                text: `${this.state.processesWithoutRisk.length} sous processus n'ont aucun risque identifié. Vérification recommandée.`
            });
        }

        return narratives;
    }

    // ============================================================
    // DONNÉES DE TEST
    // ============================================================
    loadTestData() {
        console.log("📊 loadTestData !");

        this.state.totalProcesses = 7;
        this.state.high = 7;
        this.state.medium = 0;
        this.state.low = 0;

        this.state.riskDistribution = [
            { key: 'high', label: 'Élevé', value: 7, color: '#dc3545' },
            { key: 'medium', label: 'Modéré', value: 0, color: '#ffc107' },
            { key: 'low', label: 'Faible', value: 0, color: '#28a745' }
        ];

        this.state.highRiskProcesses = [
            { id: 1, name: 'Processus A', code: 'PRC-A', count: 5, owner: 'Jean Dupont' },
            { id: 2, name: 'Processus B', code: 'PRC-B', count: 3, owner: 'Marie Martin' },
            { id: 3, name: 'Processus C', code: 'PRC-C', count: 2, owner: 'Pierre Durand' },
        ];

        this.state.topProcesses = [
            { id: 1, name: 'Processus A', code: 'PRC-A', count: 5, level: 'high', owner: 'Jean Dupont' },
            { id: 2, name: 'Processus B', code: 'PRC-B', count: 3, level: 'high', owner: 'Marie Martin' },
            { id: 3, name: 'Processus C', code: 'PRC-C', count: 2, level: 'medium', owner: 'Pierre Durand' },
        ];

        this.state.matrix = {
            'Processus de Pilotage': { high: 2, medium: 0, low: 0, total: 2 },
            'Processus Opérationnels': { high: 3, medium: 0, low: 0, total: 3 },
            'Processus Supports': { high: 2, medium: 0, low: 0, total: 2 },
        };

        this.state.categoryStats = {
            'Processus de Pilotage': 2,
            'Processus Opérationnels': 3,
            'Processus Supports': 2,
        };

        this.state.processesWithoutRisk = [];

        // Données de test : pas de vraie navigation possible (pas d'IDs réels
        // en base), on vide donc les listes d'IDs pour désactiver les clics.
        this.state.residualHighProcessIds = [];
        this.state.residualMediumProcessIds = [];
        this.state.residualLowProcessIds = [];
        this.state.inherentHighProcessIds = [];
        this.state.noRiskProcessIds = [];
        this.state.categoryProcessIds = {};
        this.state.categoryLevelProcessIds = {};

        this.state.narratives = this.generateNarratives();
    }

    // ============================================================
    // RENDU D'UN SEUL DONUT (utilisé par le template, qui gère lui-même
    // le conteneur cliquable .donut-item — cette méthode ne rend que le
    // SVG et son libellé, pour éviter d'imbriquer deux fois la même classe).
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

    // ============================================================
    // RENDU DES DONUT CHARTS (grille complète, conservé pour compatibilité
    // — non cliquable ; utilisé nulle part dans le template actuel qui
    // préfère renderSingleDonut par item pour permettre le clic)
    // ============================================================
    renderDonutChart(distribution, total) {
        if (!distribution || distribution.length === 0) {
            distribution = [
                { label: 'Élevé', value: this.state.high || 0, color: '#dc3545' },
                { label: 'Modéré', value: this.state.medium || 0, color: '#ffc107' },
                { label: 'Faible', value: this.state.low || 0, color: '#28a745' }
            ];
        }

        const circumference = 282.74;
        let html = '<div class="donut-grid">';

        distribution.forEach(item => {
            const percent = total > 0 ? item.value / total : 0;
            const offset = circumference * (1 - percent);

            html += `
                <div class="donut-item">
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
                </div>
            `;
        });

        html += '</div>';

        // 🔥 CORRIGÉ : retourner du markup
        return markup(html);
    }

    // ============================================================
    // FONCTIONS UTILITAIRES
    // ============================================================
    getLevelBadge(level) {
        const badges = {
            'high': '🔴 Élevé',
            'medium': '🟡 Modéré',
            'low': '🟢 Faible'
        };
        return badges[level] || '⚪ Inconnu';
    }

    getMaxDistribution() {
        const max = Math.max(
            this.state.high,
            this.state.medium,
            this.state.low,
            1
        );
        return max;
    }

    getCategoryMax() {
        const values = Object.values(this.state.categoryStats);
        return Math.max(...values, 1);
    }

    // ✅ CORRIGÉ : pour les catégories de risk.process
    formatCategory(category) {
        const map = {
            'pilotage': '🏛️ Processus de Pilotage',
            'operational': '⚙️ Processus Opérationnels',
            'support': '🛠️ Processus Supports'
        };
        return map[category] || category || 'Non classé';
    }

    // Renvoie la liste d'IDs de processus pour une catégorie + un niveau
    // résiduel donnés (utilisé par les cellules cliquables de la matrice).
    // ⚠️ Fonction fléchée (et non méthode de prototype) : elle est appelée
    // depuis une lambda inline dans le template (t-on-click="() => ...
    // getCategoryLevelIds(...)"), qui ne préserve pas le "this" d'une
    // méthode classique — d'où l'erreur "Cannot read properties of
    // undefined (reading 'state')" sans ce binding lexical.
    getCategoryLevelIds = (categoryLabel, level) => {
        const byCategory = this.state.categoryLevelProcessIds[categoryLabel];
        return (byCategory && byCategory[level]) || [];
    }

    // ============================================================
    // ACTIONS / NAVIGATION
    // ============================================================
    openAllProcesses = () => {
        if (this.action) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Tous les sous processus',
                res_model: 'risk.process',
                views: [[false, 'list'], [false, 'form']],
                domain: [],
            });
        } else {
            console.warn("📊 Action service non disponible");
        }
    }

    // Ouvre une liste de sous processus filtrée sur une liste d'IDs précise —
    // méthode générique utilisée par tous les indicateurs cliquables du
    // dashboard, pour garantir que ce qui s'ouvre correspond exactement à ce
    // qui est affiché (compté côté client à partir des mêmes données).
    openProcessesByIds = (ids, title) => {
        if (!this.action) {
            console.warn("📊 Action service non disponible");
            return;
        }
        if (!ids || ids.length === 0) {
            // Rien à afficher (ex. 0 sous processus à risque élevé) : pas de
            // navigation vers une liste vide.
            return;
        }
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: title,
            res_model: 'risk.process',
            views: [[false, 'list'], [false, 'form']],
            domain: [['id', 'in', ids]],
        });
    }

    // Conservée pour compatibilité, désormais basée sur la même liste d'IDs
    // que la carte KPI "Élevés" (niveau résiduel), au lieu de reconstruire un
    // domaine serveur sur un champ d'échelle différent (risk.process.risk_level,
    // 1-5) qui ne correspondait pas à ce qui est réellement affiché ici.
    openHighRiskProcesses = () => {
        this.openProcessesByIds(this.state.residualHighProcessIds, 'Sous processus à risque résiduel élevé');
    }

    openProcessById = (processId) => {
        console.log("📊 openProcessById appelé avec ID:", processId);
        if (this.action) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Détail du processus',
                res_model: 'risk.process',
                views: [[false, 'form']],
                res_id: processId,
            });
        } else {
            console.warn("📊 Action service non disponible");
        }
    }
}

console.log("📊 ProcessDashboard exporté !");

// ============================================================
// ENREGISTREMENT
// ============================================================
ProcessDashboard.template = "risk_management.process_dashboard";
registry.category('components').add('risk_management.process_dashboard', ProcessDashboard);
registry.category('actions').add('risk_management.process_dashboard', ProcessDashboard);

console.log("📊 Action process_dashboard enregistrée !");
