odoo.define('risk_management.risk_matrix_widget', function (require) {
    "use strict";

    var AbstractField = require('web.AbstractField');
    var fieldRegistry = require('web.field_registry');
    var core = require('web.core');
    var QWeb = core.qweb;

    var RiskMatrixWidget = AbstractField.extend({
        template: 'risk_management.risk_matrix',
        className: 'o_risk_matrix_widget',
        events: {
            'click .matrix-cell': '_onCellClick',
        },

        init: function (parent, name, record, options) {
            this._super.apply(this, arguments);
            // Valeurs par défaut
            this.impact = 3;
            this.probability = 3;
        },

        start: function () {
            this._super.apply(this, arguments);
            this._renderMatrix();
        },

        _render: function () {
            this._renderMatrix();
        },

        _renderMatrix: function () {
            var self = this;
            var $container = this.$('.matrix-container');
            if (!$container.length) {
                return;
            }
            $container.empty();

            var $table = $('<table class="matrix-table"/>');

            // En-tête
            var $header = $('<thead><tr><th>Probabilité ↓</th></tr></thead>');
            var $headerRow = $header.find('tr');
            for (var i = 1; i <= 5; i++) {
                $headerRow.append($('<th class="matrix-header">' + i + '</th>'));
            }
            $table.append($header);

            // Corps
            var $tbody = $('<tbody/>');
            for (var prob = 5; prob >= 1; prob--) {
                var $row = $('<tr class="matrix-row"/>');
                $row.append($('<td class="matrix-label"><strong>' + prob + '</strong></td>'));

                for (var impact = 1; impact <= 5; impact++) {
                    var score = prob * impact;
                    var $cell = $('<td class="matrix-cell"/>');
                    $cell.data('impact', impact);
                    $cell.data('probability', prob);
                    $cell.data('score', score);

                    var color = self._getColor(score);
                    $cell.css('background-color', color);
                    $cell.css('color', score > 12 ? 'white' : 'black');
                    $cell.text(score);

                    // Marquer la position actuelle
                    if (prob === self.probability && impact === self.impact) {
                        $cell.addClass('active');
                        $cell.html('<i class="fa fa-circle text-white"></i> ' + score);
                    }

                    $row.append($cell);
                }
                $tbody.append($row);
            }
            $table.append($tbody);
            $container.append($table);

            // Légende
            this._renderLegend($container);
        },

        _renderLegend: function ($container) {
            var legend = [
                { label: 'Faible (1-4)', color: '#28a745' },
                { label: 'Moyen (5-9)', color: '#ffc107' },
                { label: 'Élevé (10-16)', color: '#fd7e14' },
                { label: 'Critique (17-25)', color: '#dc3545' }
            ];

            var $legend = $('<div class="matrix-legend"/>');
            legend.forEach(function(item) {
                $legend.append(
                    $('<span class="legend-item"/>').append(
                        $('<span class="color-box"/>').css('background-color', item.color),
                        item.label
                    )
                );
            });
            $container.append($legend);
        },

        _getColor: function (score) {
            if (score <= 4) return '#28a745';
            if (score <= 9) return '#ffc107';
            if (score <= 16) return '#fd7e14';
            return '#dc3545';
        },

        _onCellClick: function (e) {
            var $cell = $(e.currentTarget);
            var impact = parseInt($cell.data('impact'));
            var probability = parseInt($cell.data('probability'));

            this.impact = impact;
            this.probability = probability;

            // Mettre à jour les champs
            this.trigger_up('field_changed', {
                name: this.name,
                value: {
                    impact_value: impact,
                    probability_value: probability
                }
            });

            this._renderMatrix();
        },

        getValue: function () {
            return {
                impact_value: this.impact,
                probability_value: this.probability
            };
        }
    });

    fieldRegistry.add('risk_matrix', RiskMatrixWidget);
    return RiskMatrixWidget;
});