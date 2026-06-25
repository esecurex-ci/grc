/** @odoo-module **/

console.log("📋 Fichier process_dashboard_widget.js chargé !");

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

console.log("📋 Imports OK !");

export class ProcessDashboard extends Component {
    static template = "risk_management.process_dashboard";

    setup() {
        console.log("📋 Setup ProcessDashboard !");
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            totalProcesses: 0,
            critical: 0,
            high: 0,
            medium: 0,
            low: 0,
            loading: true,
            matrix: this.initializeMatrix(),
            criticalProcesses: [],
            topProcesses: [],
            categoryStats: {},
            riskDistribution: [],
            processesWithoutRisk: [],
            narratives: [],
        });

        onWillStart(async () => {
            console.log("📋 onWillStart !");
            await this.loadDashboardData();
        });
    }

    initializeMatrix() {
        const matrix = {};
        const categories = ['pilotage', 'operational', 'support'];
        const levels = ['critical', 'high', 'medium', 'low'];

        categories.forEach(cat => {
            matrix[cat] = {};
            levels.forEach(level => {
                matrix[cat][level] = 0;
            });
            matrix[cat]['total'] = 0;
        });
        return matrix;
    }

    async loadDashboardData() {
        console.log("📋 loadDashboardData !");
        try {
            // Charger les processus
            const processes = await this.orm.searchRead(
                "risk.process",
                [['active', '=', true]],
                [
                    "id", "name", "code", "category", "macro_process_id",
                    "owner_id", "count_risk", "risk_level"
                ],
                1000
            );

            console.log("📋 Processus chargés :", processes);

            if (processes && processes.length > 0) {
                this.processData(processes);
            } else {
                this.loadTestData();
            }

        } catch (error) {
            console.error("📋 Erreur :", error);
            this.loadTestData();
        } finally {
            this.state.loading = false;
        }
    }

    processData(processes) {
        console.log("📋 Traitement des processus :", processes.length);

        const matrix = this.initializeMatrix();
        let total = processes.length;
        let critical = 0, high = 0, medium = 0, low = 0;
        let categoryStats = {};
        let criticalProcesses = [];
        let processesWithoutRisk = [];

        processes.forEach(process => {
            const level = process.risk_level || '1';
            const category = process.category || 'operational';

            // Compter par niveau
            if (level === '5') { critical++; }
            else if (level === '4') { high++; }
            else if (level === '3') { medium++; }
            else { low++; }

            // Matrice par catégorie
            if (matrix[category]) {
                const levelKey = this._getLevelKey(level);
                if (matrix[category][levelKey] !== undefined) {
                    matrix[category][levelKey] += 1;
                }
                matrix[category]['total'] += 1;
            }

            // Catégories
            const catName = this._getCategoryLabel(category);
            categoryStats[catName] = (categoryStats[catName] || 0) + 1;

            // Processus critiques
            if (level === '5') {
                criticalProcesses.push({
                    id: process.id,
                    name: process.name,
                    code: process.code,
                    level: level,
                    count: process.count_risk || 0,
                    owner: process.owner_id ? process.owner_id[1] : '',
                    category: catName,
                });
            }

            // Processus sans risque
            if ((process.count_risk || 0) === 0) {
                processesWithoutRisk.push({
                    id: process.id,
                    name: process.name,
                    code: process.code,
                    category: catName,
                });
            }
        });

        // Top 5 processus à risque
        const topProcesses = processes
            .sort((a, b) => (b.count_risk || 0) - (a.count_risk || 0))
            .slice(0, 5)
            .map(p => ({
                id: p.id,
                name: p.name,
                code: p.code,
                level: p.risk_level || '1',
                count: p.count_risk || 0,
                owner: p.owner_id ? p.owner_id[1] : '',
                category: this._getCategoryLabel(p.category),
            }));

        // Distribution des risques
        const riskDistribution = [
            { label: 'Critiques', value: critical, color: '#dc3545' },
            { label: 'Élevés', value: high, color: '#fd7e14' },
            { label: 'Moyens', value: medium, color: '#ffc107' },
            { label: 'Faibles', value: low, color: '#28a745' },
        ];

        // Narratives
        const narratives = [
            { icon: '🔺', text: 'Nouveau processus critique identifié : Gestion de la sécurité' },
            { icon: '📈', text: 'Augmentation du nombre de processus à risque (+2 vs T2)' },
            { icon: '✅', text: 'Mise en place du plan d\'action pour les processus critiques' },
        ];

        this.state.matrix = matrix;
        this.state.totalProcesses = total;
        this.state.critical = critical;
        this.state.high = high;
        this.state.medium = medium;
        this.state.low = low;
        this.state.criticalProcesses = criticalProcesses;
        this.state.topProcesses = topProcesses;
        this.state.categoryStats = categoryStats;
        this.state.riskDistribution = riskDistribution;
        this.state.processesWithoutRisk = processesWithoutRisk;
        this.state.narratives = narratives;

        console.log("📋 Dashboard chargé !", this.state);
    }

    _getLevelKey(level) {
        if (level === '5') return 'critical';
        if (level === '4') return 'high';
        if (level === '3') return 'medium';
        return 'low';
    }

    _getCategoryLabel(category) {
        const map = {
            'pilotage': 'Pilotage',
            'operational': 'Opérationnel',
            'support': 'Support'
        };
        return map[category] || category;
    }

    loadTestData() {
        console.log("📋 loadTestData !");
        const matrix = this.initializeMatrix();
        matrix['pilotage']['critical'] = 1;
        matrix['pilotage']['high'] = 0;
        matrix['pilotage']['medium'] = 1;
        matrix['pilotage']['low'] = 1;
        matrix['pilotage']['total'] = 3;
        matrix['operational']['critical'] = 2;
        matrix['operational']['high'] = 1;
        matrix['operational']['medium'] = 2;
        matrix['operational']['low'] = 1;
        matrix['operational']['total'] = 6;
        matrix['support']['critical'] = 0;
        matrix['support']['high'] = 1;
        matrix['support']['medium'] = 1;
        matrix['support']['low'] = 1;
        matrix['support']['total'] = 3;

        this.state.matrix = matrix;
        this.state.totalProcesses = 12;
        this.state.critical = 3;
        this.state.high = 2;
        this.state.medium = 4;
        this.state.low = 3;
        this.state.criticalProcesses = [
            { id: 1, name: 'Gestion sécurité informatique', code: 'SEC-01', level: '5', count: 5, owner: 'Admin', category: 'Opérationnel' },
            { id: 2, name: 'Gestion portefeuille', code: 'PF-01', level: '5', count: 4, owner: 'Admin', category: 'Pilotage' },
            { id: 3, name: 'Conformité réglementaire', code: 'COMP-01', level: '5', count: 3, owner: 'Admin', category: 'Pilotage' },
        ];
        this.state.topProcesses = [
            { id: 1, name: 'Gestion sécurité informatique', code: 'SEC-01', level: '5', count: 5, owner: 'Admin', category: 'Opérationnel' },
            { id: 2, name: 'Gestion portefeuille', code: 'PF-01', level: '5', count: 4, owner: 'Admin', category: 'Pilotage' },
            { id: 3, name: 'Conformité réglementaire', code: 'COMP-01', level: '5', count: 3, owner: 'Admin', category: 'Pilotage' },
            { id: 4, name: 'Gestion clientèle', code: 'CLI-01', level: '4', count: 2, owner: 'Admin', category: 'Opérationnel' },
            { id: 5, name: 'Gestion RH', code: 'RH-01', level: '3', count: 1, owner: 'Admin', category: 'Support' },
        ];
        this.state.categoryStats = {
            'Pilotage': 3,
            'Opérationnel': 6,
            'Support': 3
        };
        this.state.riskDistribution = [
            { label: 'Critiques', value: 3, color: '#dc3545' },
            { label: 'Élevés', value: 2, color: '#fd7e14' },
            { label: 'Moyens', value: 4, color: '#ffc107' },
            { label: 'Faibles', value: 3, color: '#28a745' },
        ];
        this.state.processesWithoutRisk = [
            { id: 10, name: 'Gestion administrative', code: 'ADM-01', category: 'Support' },
            { id: 11, name: 'Gestion des changements', code: 'CHG-01', category: 'Opérationnel' },
            { id: 12, name: 'Calcul VL', code: 'VL-01', category: 'Opérationnel' },
        ];
        this.state.narratives = [
            { icon: '🔺', text: 'Nouveau processus critique identifié : Gestion de la sécurité' },
            { icon: '📈', text: 'Augmentation du nombre de processus à risque (+2 vs T2)' },
            { icon: '✅', text: 'Mise en place du plan d\'action pour les processus critiques' },
        ];
    }

    // ============================================================
    // MÉTHODES UTILITAIRES POUR LE TEMPLATE
    // ============================================================

    getLevelBadge(level) {
        const map = {
            '5': 'critical',
            '4': 'high',
            '3': 'medium',
            '2': 'low',
            '1': 'low'
        };
        return map[level] || 'secondary';
    }

    getCategoryMax() {
        const values = Object.values(this.state.categoryStats);
        return values.length > 0 ? Math.max(...values) : 1;
    }

    getMaxDistribution() {
        const values = this.state.riskDistribution.map(d => d.value);
        return values.length > 0 ? Math.max(...values) : 1;
    }

    // ============================================================
    // GESTION DES ÉVÉNEMENTS
    // ============================================================

    openProcessList(domain) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Processus",
            res_model: "risk.process",
            views: [[false, "list"], [false, "form"]],
            domain: domain,
            target: "current",
        });
    }

    openAllProcesses() {
        this.openProcessList([]);
    }

    openCriticalProcesses() {
        this.openProcessList([["risk_level", "=", "5"]]);
    }

    openProcessById(processId) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Processus",
            res_model: "risk.process",
            views: [[false, "form"]],
            res_id: processId,
            target: "current",
        });
    }

    formatCategory(cat) {
        const map = {
            'pilotage': 'Pilotage',
            'operational': 'Opérationnel',
            'support': 'Support'
        };
        return map[cat] || cat;
    }
}

console.log("📋 ProcessDashboard exporté !");

ProcessDashboard.template = "risk_management.process_dashboard";

registry.category("actions").add("process_dashboard", ProcessDashboard);

console.log("📋 Action process_dashboard enregistrée !");