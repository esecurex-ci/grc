odoo.define('risk_management.risk_dashboard_heatmap', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');

    var RiskDashboardHeatmap = AbstractField.extend({
        template: 'risk_management.risk_dashboard_heatmap',
        className: 'o_risk_dashboard_heatmap',

        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            this.risks = [];
        },

        start: function () {
            this._super.apply(this, arguments);
            this._loadRisks();
        },

        _loadRisks: function () {
            var self = this;
            this._rpc({
                model: 'risk.risk',
                method: 'search_read',
                args: [[]],
                kwargs: {
                    fields: ['id', 'name', 'code', 'inherent_impact', 'inherent_probability', 'inherent_level', 'inherent_score'],
                    domain: [['active', '=', True]]
                }
            }).then(function (result) {
                self.risks = result;
                self._renderHeatmap();
                self._renderKPI();
            });
        },

        _renderKPI: function () {
            var self = this;
            var $container = this.$('.kpi-container');
            $container.empty();

            var total = this.risks.length;
            var critical = this.risks.filter(function(r) { return r.inherent_level === 'critical'; }).length;
            var high = this.risks.filter(function(r) { return r.inherent_level === 'high'; }).length;
            var medium = this.risks.filter(function(r) { return r.inherent_level === 'medium'; }).length;
            var low = this.risks.filter(function(r) { return r.inherent_level === 'low'; }).length;

            var kpis = [
                { label: 'Total Risques', value: total, class: 'total' },
                { label: 'Critiques', value: critical, class: 'critical' },
                { label: 'Élevés', value: high, class: 'high' },
                { label: 'Moyens', value: medium, class: 'medium' },
                { label: 'Faibles', value: low, class: 'low' }
            ];

            kpis.forEach(function(kpi) {
                var $card = $('<div class="kpi-card ' + kpi.class + '"/>');
                $card.append('<div class="kpi-value">' + kpi.value + '</div>');
                $card.append('<div class="kpi-label">' + kpi.label + '</div>');
                $container.append($card);
            });
        },

        _renderHeatmap: function () {
            var self = this;
            var $container = this.$('.heatmap-container');
            $container.empty();

            var $title = $('<div class="heatmap-title">🔥 Carte de chaleur - Fréquence × Gravité</div>');
            $container.append($title);

            var $table = $('<table class="heatmap-table"/>');

            var $header = $('<tr/>');
            $header.append('<th class="heatmap-label">Gravité →</th>');
            for (var i = 1; i <= 5; i++) {
                $header.append('<th class="heatmap-header">' + i + '</th>');
            }
            $table.append($header);

            for (var prob = 5; prob >= 1; prob--) {
                var $row = $('<tr/>');
                $row.append('<td class="heatmap-label">' + prob + '</td>');

                for (var impact = 1; impact <= 5; impact++) {
                    var score = prob * impact;
                    var color = self._getColor(score);
                    var $cell = $('<td class="heatmap-cell"/>');
                    $cell.css('background-color', color);
                    $cell.data('impact', impact);
                    $cell.data('probability', prob);

                    var risksInCell = self.risks.filter(function(r) {
                        return parseInt(r.inherent_impact) === impact &&
                               parseInt(r.inherent_probability) === prob;
                    });

                    if (risksInCell.length > 0) {
                        $cell.addClass('has-risks');
                        $cell.html('<span class="risk-count">' + risksInCell.length + '</span>');
                        $cell.attr('title', risksInCell.map(function(r) {
                            return r.code + ' - ' + r.name + ' (' + r.inherent_level + ')';
                        }).join('\n'));
                        $cell.data('risks', risksInCell);

                        $cell.on('click', function(e) {
                            var risks = $(this).data('risks');
                            if (risks && risks.length > 0) {
                                var riskIds = risks.map(function(r) { return r.id; });
                                self.do_action({
                                    type: 'ir.actions.act_window',
                                    name: 'Risques filtrés',
                                    res_model: 'risk.risk',
                                    view_mode: 'list',
                                    domain: [['id', 'in', riskIds]]
                                });
                            }
                        });
                    } else {
                        $cell.html('&nbsp;');
                    }

                    $row.append($cell);
                }
                $table.append($row);
            }

            $container.append($table);

            var $legend = $('<div class="heatmap-legend"/>');
            var legendItems = [
                { label: 'Faible (1-4)', color: '#28a745' },
                { label: 'Moyen (5-9)', color: '#ffc107' },
                { label: 'Élevé (10-16)', color: '#fd7e14' },
                { label: 'Critique (17-25)', color: '#dc3545' }
            ];
            legendItems.forEach(function(item) {
                $legend.append(
                    $('<span class="legend-item"/>').append(
                        $('<span class="color-box"/>').css('background-color', item.color),
                        item.label
                    )
                );
            });
            $container.append($legend);

            $container.append('<div class="heatmap-total">📊 Total: ' + this.risks.length + ' risques</div>');
        },

        _getColor: function (score) {
            if (score <= 4) return '#28a745';
            if (score <= 9) return '#ffc107';
            if (score <= 16) return '#fd7e14';
            return '#dc3545';
        }
    });

    // ⚠️ IMPORTANT : Le nom enregistré doit correspondre à celui utilisé dans le XML
    fieldRegistry.add('risk_dashboard_heatmap', RiskDashboardHeatmap);
    return RiskDashboardHeatmap;

    console.log('🔥 Loading risk_dashboard_heatmap.js...');

    odoo.define('risk_management.risk_dashboard_heatmap', function (require) {
        console.log('🔥 risk_dashboard_heatmap module loaded!');
        // ... le reste du code
});
});