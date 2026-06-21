odoo.define('risk_management.risk_dashboard_kpi_widget', function (require) {
    "use strict";

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core');

    var RiskDashboardKPI = AbstractAction.extend({
        template: 'risk_management.risk_dashboard_kpi',
        className: 'o_risk_dashboard_kpi',

        start: function () {
            console.log('🚀 Dashboard KPI widget started!');
            this._super.apply(this, arguments);
            this._loadDashboard();
            return this._super.apply(this, arguments);
        },

        _loadDashboard: function () {
            var self = this;
            console.log('📊 Loading dashboard...');
            this._rpc({
                model: 'risk.risk',
                method: 'get_dashboard_html'
            }).then(function (result) {
                console.log('✅ Dashboard loaded!');
                self.$('.dashboard-content').html(result);
            }).catch(function (error) {
                console.error('❌ Error loading dashboard:', error);
                self.$('.dashboard-content').html('<div style="padding:40px;text-align:center;color:#dc3545;">❌ Erreur: ' + error.message + '</div>');
            });
        }
    });

    core.action_registry.add('risk_dashboard_kpi', RiskDashboardKPI);
    console.log('✅ Widget risk_dashboard_kpi registered!');
    return RiskDashboardKPI;
});