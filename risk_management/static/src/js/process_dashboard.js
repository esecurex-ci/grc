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
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
            riskDistribution: [],
            criticalProcesses: [],
            topProcesses: [],
            processesWithoutRisk: [],
            matrix: {},
            categoryStats: {},
            narratives: []
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

            // ✅ CORRIGÉ : utiliser inherent_level au lieu de severity
            const criticalCount = processRisks.filter(r => r.inherent_level === 'critical').length;
            const highCount = processRisks.filter(r => r.inherent_level === 'high').length;
            const mediumCount = processRisks.filter(r => r.inherent_level === 'medium').length;
            const lowCount = processRisks.filter(r => r.inherent_level === 'low').length;

            // Déterminer le niveau global du processus
            let level = 'low';
            if (criticalCount > 0) level = 'critical';
            else if (highCount > 0) level = 'high';
            else if (mediumCount > 0) level = 'medium';

            // ✅ CORRIGÉ : utiliser le champ 'category' (Selection) directement
            const category = process.category || 'operational';
            const categoryLabel = this.formatCategory(category);

            processLevels[process.id] = {
                ...process,
                riskCount: processRisks.length,
                criticalCount,
                highCount,
                mediumCount,
                lowCount,
                level,
                categoryLabel
            };

            // Statistiques par catégorie
            if (!categories[categoryLabel]) {
                categories[categoryLabel] = { critical: 0, high: 0, medium: 0, low: 0, total: 0 };
            }
            categories[categoryLabel][level]++;
            categories[categoryLabel].total++;
        });

        // ============================================================
        // 1. KPI CARDS
        // ============================================================
        this.state.totalProcesses = processes.length;
        this.state.critical = Object.values(processLevels).filter(p => p.level === 'critical').length;
        this.state.high = Object.values(processLevels).filter(p => p.level === 'high').length;
        this.state.medium = Object.values(processLevels).filter(p => p.level === 'medium').length;
        this.state.low = Object.values(processLevels).filter(p => p.level === 'low').length;

        // ============================================================
        // 2. RISK DISTRIBUTION (pour les Donuts)
        // ============================================================
        this.state.riskDistribution = [
            { label: 'Critique', value: this.state.critical, color: '#dc3545' },
            { label: 'Élevé', value: this.state.high, color: '#fd7e14' },
            { label: 'Moyen', value: this.state.medium, color: '#ffc107' },
            { label: 'Faible', value: this.state.low, color: '#28a745' }
        ];

        // ============================================================
        // 3. PROCESSUS CRITIQUES
        // ============================================================
        this.state.criticalProcesses = Object.values(processLevels)
            .filter(p => p.level === 'critical')
            .map(p => ({
                id: p.id,
                name: p.name,
                code: p.code || 'N/A',
                count: p.riskCount,
                owner: p.owner_id ? p.owner_id[1] : 'Non assigné'
            }))
            .slice(0, 10);

        // ============================================================
        // 4. TOP 5 PROCESSUS À RISQUE
        // ============================================================
        this.state.topProcesses = Object.values(processLevels)
            .sort((a, b) => b.riskCount - a.riskCount)
            .slice(0, 5)
            .map(p => ({
                id: p.id,
                name: p.name,
                code: p.code || 'N/A',
                count: p.riskCount,
                level: p.level,
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

        if (this.state.critical > 0) {
            narratives.push({
                icon: '🔴',
                text: `${this.state.critical} processus sont critiques : une attention immédiate est requise.`
            });
        }

        if (this.state.high > 0) {
            narratives.push({
                icon: '🟠',
                text: `${this.state.high} processus ont un niveau de risque élevé.`
            });
        }

        const totalRisky = this.state.critical + this.state.high;
        if (totalRisky === 0) {
            narratives.push({
                icon: '✅',
                text: 'Aucun processus à risque critique ou élevé. Bonne maîtrise des risques !'
            });
        } else if (totalRisky > this.state.totalProcesses * 0.5) {
            narratives.push({
                icon: '⚠️',
                text: `Plus de 50% des processus (${totalRisky}/${this.state.totalProcesses}) présentent des risques critiques ou élevés.`
            });
        }

        if (this.state.processesWithoutRisk.length > 0) {
            narratives.push({
                icon: '📋',
                text: `${this.state.processesWithoutRisk.length} processus n'ont aucun risque identifié. Vérification recommandée.`
            });
        }

        if (narratives.length === 0) {
            narratives.push({
                icon: '📊',
                text: 'Aucun changement significatif détecté. Les processus sont sous contrôle.'
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
        this.state.critical = 7;
        this.state.high = 0;
        this.state.medium = 0;
        this.state.low = 0;

        this.state.riskDistribution = [
            { label: 'Critique', value: 7, color: '#dc3545' },
            { label: 'Élevé', value: 0, color: '#fd7e14' },
            { label: 'Moyen', value: 0, color: '#ffc107' },
            { label: 'Faible', value: 0, color: '#28a745' }
        ];

        this.state.criticalProcesses = [
            { id: 1, name: 'Processus A', code: 'PRC-A', count: 5, owner: 'Jean Dupont' },
            { id: 2, name: 'Processus B', code: 'PRC-B', count: 3, owner: 'Marie Martin' },
            { id: 3, name: 'Processus C', code: 'PRC-C', count: 2, owner: 'Pierre Durand' },
        ];

        this.state.topProcesses = [
            { id: 1, name: 'Processus A', code: 'PRC-A', count: 5, level: 'critical', owner: 'Jean Dupont' },
            { id: 2, name: 'Processus B', code: 'PRC-B', count: 3, level: 'high', owner: 'Marie Martin' },
            { id: 3, name: 'Processus C', code: 'PRC-C', count: 2, level: 'medium', owner: 'Pierre Durand' },
        ];

        this.state.matrix = {
            'Processus de Pilotage': { critical: 2, high: 0, medium: 0, low: 0, total: 2 },
            'Processus Opérationnels': { critical: 3, high: 0, medium: 0, low: 0, total: 3 },
            'Processus Supports': { critical: 2, high: 0, medium: 0, low: 0, total: 2 },
        };

        this.state.categoryStats = {
            'Processus de Pilotage': 2,
            'Processus Opérationnels': 3,
            'Processus Supports': 2,
        };

        this.state.processesWithoutRisk = [];
        this.state.narratives = this.generateNarratives();
    }

    // ============================================================
    // RENDU DES DONUT CHARTS
    // ============================================================
    renderDonutChart(distribution, total) {
        if (!distribution || distribution.length === 0) {
            distribution = [
                { label: 'Critique', value: this.state.critical || 0, color: '#dc3545' },
                { label: 'Élevé', value: this.state.high || 0, color: '#fd7e14' },
                { label: 'Moyen', value: this.state.medium || 0, color: '#ffc107' },
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
            'critical': '🔴 Critique',
            'high': '🟠 Élevé',
            'medium': '🟡 Moyen',
            'low': '🟢 Faible'
        };
        return badges[level] || '⚪ Inconnu';
    }

    getMaxDistribution() {
        const max = Math.max(
            this.state.critical,
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

    // ============================================================
    // ACTIONS / NAVIGATION
    // ============================================================
    openAllProcesses = () => {
        if (this.action) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Tous les processus',
                res_model: 'risk.process',
                views: [[false, 'list'], [false, 'form']],
                domain: [],
            });
        } else {
            console.warn("📊 Action service non disponible");
        }
    }

    openCriticalProcesses = () => {
        if (this.action) {
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Processus critiques',
                res_model: 'risk.process',
                views: [[false, 'list'], [false, 'form']],
                domain: [['risk_level', '=', '5']],
            });
        } else {
            console.warn("📊 Action service non disponible");
        }
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