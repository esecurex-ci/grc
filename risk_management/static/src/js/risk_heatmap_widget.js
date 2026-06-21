odoo.define('risk_management.risk_heatmap_widget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');
    var QWeb = core.qweb;

    var RiskHeatmapWidget = AbstractField.extend({
        template: 'risk_management.risk_heatmap',
        className: 'o_risk_heatmap_widget',
        events: {
            'mouseenter .heatmap-cell': '_onCellHover',
            'mouseleave .heatmap-cell': '_onCellLeave',
            'click .heatmap-cell': '_onCellClick',
        },

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
                    fields: ['id', 'name', 'code', 'inherent_impact', 'inherent_probability', 'inherent_level', 'category_id'],
                    domain: [['active', '=', True]]
                }
            }).then(function (result) {
                self.risks = result;
                self._renderHeatmap();
            });
        },

        _renderHeatmap: function () {
            var self = this;
            var $container = this.$('.heatmap-container');
            $container.empty();

            // Créer la matrice 5x5
            var $matrix = $('<div class="heatmap-matrix"/>');

            // En-tête
            var $header = $('<div class="heatmap-header"/>');
            $header.append('<div class="heatmap-label">Gravité →</div>');
            for (var i = 1; i <= 5; i++) {
                $header.append($('<div class="heatmap-header-cell">' + i + '</div>'));
            }
            $matrix.append($header);

            // Corps de la matrice
            for (var prob = 5; prob >= 1; prob--) {
                var $row = $('<div class="heatmap-row"/>');
                $row.append($('<div class="heatmap-label">' + prob + '</div>'));

                for (var impact = 1; impact <= 5; impact++) {
                    var score = prob * impact;
                    var color = self._getColor(score);
                    var $cell = $('<div class="heatmap-cell"/>');
                    $cell.css('background-color', color);
                    $cell.data('impact', impact);
                    $cell.data('probability', prob);
                    $cell.data('score', score);

                    // Trouver les risques dans cette cellule
                    var risksInCell = self.risks.filter(function(r) {
                        return parseInt(r.inherent_impact) === impact &&
                               parseInt(r.inherent_probability) === prob;
                    });

                    if (risksInCell.length > 0) {
                        $cell.addClass('has-risks');
                        $cell.html('<span class="risk-count">' + risksInCell.length + '</span>');

                        // Stocker les risques pour le tooltip
                        var tooltipText = risksInCell.map(function(r) {
                            return r.code + ' - ' + r.name;
                        }).join('\n');
                        $cell.attr('title', tooltipText);
                        $cell.data('risks', risksInCell);
                    } else {
                        $cell.html('&nbsp;');
                    }

                    $row.append($cell);
                }
                $matrix.append($row);
            }

            // Légende
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

            $container.append($matrix);
            $container.append($legend);

            // Ajouter le total des risques
            $container.append('<div class="heatmap-total">Total des risques: ' + this.risks.length + '</div>');
        },

        _getColor: function (score) {
            if (score <= 4) return '#28a745';
            if (score <= 9) return '#ffc107';
            if (score <= 16) return '#fd7e14';
            return '#dc3545';
        },

        _onCellHover: function (e) {
            var $cell = $(e.currentTarget);
            var risks = $cell.data('risks');
            if (risks && risks.length > 0) {
                // Afficher un tooltip personnalisé
                var tooltip = risks.map(function(r) {
                    return r.code + ' - ' + r.name + ' (' + r.inherent_level + ')';
                }).join('<br/>');

                var $tooltip = $('<div class="heatmap-tooltip"/>').html(tooltip);
                $('body').append($tooltip);

                var pos = $cell.offset();
                $tooltip.css({
                    left: pos.left + $cell.outerWidth() / 2 - $tooltip.outerWidth() / 2,
                    top: pos.top - $tooltip.outerHeight() - 10
                });
            }
        },

        _onCellLeave: function (e) {
            $('.heatmap-tooltip').remove();
        },

        _onCellClick: function (e) {
            var $cell = $(e.currentTarget);
            var risks = $cell.data('risks');
            if (risks && risks.length > 0) {
                // Ouvrir la vue liste filtrée
                var riskIds = risks.map(function(r) { return r.id; });
                this.do_action({
                    type: 'ir.actions.act_window',
                    name: 'Risques filtrés',
                    res_model: 'risk.risk',
                    view_mode: 'list',
                    domain: [['id', 'in', riskIds]]
                });
            }
        }
    });

    fieldRegistry.add('risk_heatmap', RiskHeatmapWidget);
    return RiskHeatmapWidget;
});
