/** @odoo-module **/

console.log("📊 Fichier kri_dashboard.js chargé !");

import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

console.log("📊 Imports OK !");

export class KriDashboard extends Component {
    static props = {
        '*': { type: Object, optional: true },
    };
    static template = "risk_management.kri_dashboard";

    setup() {
        console.log("📊 Setup KriDashboard !");
        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({
            loading: true,
            totalKris: 0,
            green: 0,
            amber: 0,
            red: 0,
            overdue: 0,
            kris: [],
            statusDistribution: [],
            categoryDistribution: [],
            recentAlerts: [],
            topWorst: [],
            trends: [],
            narratives: [],
        });

        onWillStart(async () => {
            console.log("📊 onWillStart !");
            await this.loadDashboardData();
        });
    }

    // ============================================================
    // CHARGEMENT DES DONNÉES
    // ============================================================
    async loadDashboardData() {
        console.log("📊 loadDashboardData !");
        try {
            const kris = await this.orm.searchRead(
                'risk.kri',
                [],
                [
                    'id', 'name', 'code', 'category', 'owner_id',
                    'current_value', 'unit', 'status', 'trend', 'variation',
                    'threshold_green', 'threshold_amber', 'threshold_red',
                    'last_measure_date', 'next_measure_date', 'overdue',
                    'alert_count', 'last_alert_date',
                    'measure_ids', 'risk_ids'
                ],
                { limit: 100 }
            );

            console.log("📊 KRI bruts :", kris);

            if (kris && kris.length > 0) {
                this.processData(kris);
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
    // TRAITEMENT DES DONNÉES
    // ============================================================
    processData(kris) {
        const total = kris.length;
        const green = kris.filter(k => k.status === 'green').length;
        const amber = kris.filter(k => k.status === 'amber').length;
        const red = kris.filter(k => k.status === 'red').length;
        const overdue = kris.filter(k => k.overdue === true).length;

        // Distribution par statut
        const statusDistribution = [
            { label: '🟢 Vert', value: green, color: '#28a745' },
            { label: '🟡 Orange', value: amber, color: '#ffc107' },
            { label: '🔴 Rouge', value: red, color: '#dc3545' },
        ];

        // Distribution par catégorie
        const categoryMap = {};
        kris.forEach(k => {
            const cat = k.category || 'Non catégorisé';
            if (!categoryMap[cat]) categoryMap[cat] = 0;
            categoryMap[cat]++;
        });
        const categoryDistribution = Object.entries(categoryMap).map(([label, value]) => ({
            label: this.formatCategory(label),
            value: value,
        }));

        // Alertes récentes (top 5)
        const recentAlerts = kris
            .filter(k => k.status === 'red' || k.status === 'amber')
            .sort((a, b) => {
                const dateA = a.last_alert_date || a.last_measure_date || '';
                const dateB = b.last_alert_date || b.last_measure_date || '';
                return dateB.localeCompare(dateA);
            })
            .slice(0, 5)
            .map(k => ({
                id: k.id,
                name: k.name,
                code: k.code,
                status: k.status,
                value: k.current_value,
                unit: k.unit,
                threshold: k.status === 'red' ? k.threshold_red : k.threshold_amber,
                date: k.last_alert_date || k.last_measure_date,
                owner: k.owner_id ? k.owner_id[1] : 'N/A',
            }));

        // Top 5 pires KRI (par valeur)
        const topWorst = kris
            .filter(k => k.status === 'red' || k.status === 'amber')
            .sort((a, b) => b.current_value - a.current_value)
            .slice(0, 5)
            .map(k => ({
                id: k.id,
                name: k.name,
                code: k.code,
                value: k.current_value,
                unit: k.unit,
                status: k.status,
                owner: k.owner_id ? k.owner_id[1] : 'N/A',
            }));

        // Tendances
        const trends = {
            'up': kris.filter(k => k.trend === 'up').length,
            'down': kris.filter(k => k.trend === 'down').length,
            'stable': kris.filter(k => k.trend === 'stable').length,
        };

        this.state.totalKris = total;
        this.state.green = green;
        this.state.amber = amber;
        this.state.red = red;
        this.state.overdue = overdue;
        this.state.kris = kris;
        this.state.statusDistribution = statusDistribution;
        this.state.categoryDistribution = categoryDistribution;
        this.state.recentAlerts = recentAlerts;
        this.state.topWorst = topWorst;
        this.state.trends = trends;
        this.state.narratives = this.generateNarratives();

        console.log("📊 Dashboard KRI chargé !", this.state);
    }

    // ============================================================
    // RAPPORT NARRATIF
    // ============================================================
    generateNarratives() {
        const narratives = [];

        if (this.state.red > 0) {
            narratives.push({
                icon: '🔴',
                text: `${this.state.red} KRI sont en alerte rouge : action immédiate requise !`
            });
        }

        if (this.state.amber > 0) {
            narratives.push({
                icon: '🟡',
                text: `${this.state.amber} KRI sont en alerte orange : surveillance renforcée.`
            });
        }

        if (this.state.overdue > 0) {
            narratives.push({
                icon: '⏰',
                text: `${this.state.overdue} KRI n'ont pas été mesurés dans les délais.`
            });
        }

        const totalBad = this.state.red + this.state.amber;
        if (totalBad === 0) {
            narratives.push({
                icon: '✅',
                text: 'Tous les KRI sont dans le vert. Excellent contrôle des risques !'
            });
        } else if (totalBad > this.state.totalKris * 0.3) {
            narratives.push({
                icon: '⚠️',
                text: `Plus de 30% des KRI (${totalBad}/${this.state.totalKris}) sont en alerte.`
            });
        }

        if (this.state.trends.up > this.state.trends.down) {
            narratives.push({
                icon: '📈',
                text: `${this.state.trends.up - this.state.trends.down} KRI supplémentaires sont en hausse.`
            });
        }

        if (narratives.length === 0) {
            narratives.push({
                icon: '📊',
                text: 'Aucune anomalie détectée. Les KRI sont sous contrôle.'
            });
        }

        return narratives;
    }

    // ============================================================
    // DONNÉES DE TEST
    // ============================================================
    loadTestData() {
        console.log("📊 loadTestData KRI !");

        this.state.totalKris = 12;
        this.state.green = 6;
        this.state.amber = 3;
        this.state.red = 3;
        this.state.overdue = 2;

        this.state.statusDistribution = [
            { label: '🟢 Vert', value: 6, color: '#28a745' },
            { label: '🟡 Orange', value: 3, color: '#ffc107' },
            { label: '🔴 Rouge', value: 3, color: '#dc3545' },
        ];

        this.state.categoryDistribution = [
            { label: '💰 Financier', value: 4 },
            { label: '⚙️ Opérationnel', value: 3 },
            { label: '📋 Conformité', value: 3 },
            { label: '🔒 Cybersécurité', value: 2 },
        ];

        this.state.recentAlerts = [
            { id: 1, name: 'Taux d\'incidents Cyber', code: 'KRI-001', status: 'red', value: 85, unit: '%', threshold: 80, date: '2024-01-15', owner: 'Jean Dupont' },
            { id: 2, name: 'Taux de conformité réglementaire', code: 'KRI-002', status: 'amber', value: 65, unit: '%', threshold: 70, date: '2024-01-14', owner: 'Marie Martin' },
            { id: 3, name: 'Nombre de contrôles défaillants', code: 'KRI-003', status: 'red', value: 12, unit: '', threshold: 10, date: '2024-01-13', owner: 'Pierre Durand' },
            { id: 4, name: 'Temps moyen de résolution', code: 'KRI-004', status: 'amber', value: 8, unit: 'jrs', threshold: 5, date: '2024-01-12', owner: 'Sophie Bernard' },
            { id: 5, name: 'Taux de rotation du personnel', code: 'KRI-005', status: 'red', value: 18, unit: '%', threshold: 15, date: '2024-01-11', owner: 'Luc Dubois' },
        ];

        this.state.topWorst = [
            { id: 1, name: 'Taux d\'incidents Cyber', code: 'KRI-001', value: 85, unit: '%', status: 'red', owner: 'Jean Dupont' },
            { id: 2, name: 'Nombre de contrôles défaillants', code: 'KRI-003', value: 12, unit: '', status: 'red', owner: 'Pierre Durand' },
            { id: 3, name: 'Taux de rotation du personnel', code: 'KRI-005', value: 18, unit: '%', status: 'red', owner: 'Luc Dubois' },
            { id: 4, name: 'Taux de conformité réglementaire', code: 'KRI-002', value: 65, unit: '%', status: 'amber', owner: 'Marie Martin' },
            { id: 5, name: 'Temps moyen de résolution', code: 'KRI-004', value: 8, unit: 'jrs', status: 'amber', owner: 'Sophie Bernard' },
        ];

        this.state.trends = { up: 4, down: 3, stable: 5 };
        this.state.narratives = this.generateNarratives();
    }

    // ============================================================
    // RENDU DES DONUT CHARTS
    // ============================================================
    renderDonutChart(data, total) {
        if (!data || data.length === 0) {
            return markup('<div class="text-muted">Aucune donnée</div>');
        }

        const circumference = 282.74;
        let html = '<div class="donut-grid">';

        data.forEach(item => {
            const percent = total > 0 ? item.value / total : 0;
            const offset = circumference * (1 - percent);

            html += `
                <div class="donut-item">
                    <div class="donut-circle">
                        <svg viewBox="0 0 120 120" width="120" height="120">
                            <circle cx="60" cy="60" r="45" fill="none" stroke="#f0f0f0" stroke-width="12"/>
                            <circle cx="60" cy="60" r="45" fill="none"
                                    stroke="${item.color || '#6c757d'}" stroke-width="12"
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
                        <span class="donut-color" style="background:${item.color || '#6c757d'};"></span>
                        ${item.label} (${item.value})
                    </div>
                </div>
            `;
        });

        html += '</div>';
        return markup(html);
    }

    // ============================================================
    // FONCTIONS UTILITAIRES
    // ============================================================
    formatCategory(category) {
        const map = {
            'financial': '💰 Financier',
            'operational': '⚙️ Opérationnel',
            'compliance': '📋 Conformité',
            'strategic': '🎯 Stratégique',
            'cyber': '🔒 Cybersécurité',
            'reputation': '📢 Réputation',
        };
        return map[category] || category || 'Non catégorisé';
    }

    getStatusBadge(status) {
        const badges = {
            'green': '🟢 Vert',
            'amber': '🟡 Orange',
            'red': '🔴 Rouge',
        };
        return badges[status] || status;
    }

    getStatusClass(status) {
        const classes = {
            'green': 'badge-success',
            'amber': 'badge-warning',
            'red': 'badge-danger',
        };
        return classes[status] || 'badge-secondary';
    }

    getTrendBadge(trend) {
        const badges = {
            'up': '📈 En hausse',
            'down': '📉 En baisse',
            'stable': '➡️ Stable',
        };
        return badges[trend] || trend;
    }

    getMaxValue(data) {
        if (!data || data.length === 0) return 1;
        return Math.max(...data.map(d => d.value));
    }

    // ============================================================
    // ACTIONS / NAVIGATION
    // ============================================================
    openAllKris() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Tous les KRI',
            res_model: 'risk.kri',
            views: [[false, 'kanban'], [false, 'tree'], [false, 'form']],
            domain: [],
        });
    }

    openRedKris() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'KRI Rouges',
            res_model: 'risk.kri',
            views: [[false, 'tree'], [false, 'form']],
            domain: [['status', '=', 'red']],
        });
    }

    openAmberKris() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'KRI Oranges',
            res_model: 'risk.kri',
            views: [[false, 'tree'], [false, 'form']],
            domain: [['status', '=', 'amber']],
        });
    }

    openOverdueKris() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'KRI en retard',
            res_model: 'risk.kri',
            views: [[false, 'tree'], [false, 'form']],
            domain: [['overdue', '=', true]],
        });
    }

    openKriById(kriId) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Détail du KRI',
            res_model: 'risk.kri',
            views: [[false, 'form']],
            res_id: kriId,
        });
    }
}

console.log("📊 KriDashboard exporté !");

// ============================================================
// ENREGISTREMENT
// ============================================================
KriDashboard.template = "risk_management.kri_dashboard";
registry.category('components').add('risk_management.kri_dashboard', KriDashboard);
registry.category('actions').add('risk_management.kri_dashboard', KriDashboard);

console.log("📊 Action kri_dashboard enregistrée !");