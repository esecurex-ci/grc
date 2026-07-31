# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import json
import logging

_logger = logging.getLogger(__name__)


class RiskKriFormulaTemplate(models.Model):
    _name = 'risk.kri.formula.template'
    _description = 'Modèle de formule KRI'
    _order = 'name'

    name = fields.Char(string='Nom du modèle', required=True)
    description = fields.Text(string='Description')
    category = fields.Selection([
        ('financial', '💰 Financier'),
        ('operational', '⚙️ Opérationnel'),
        ('compliance', '📋 Conformité'),
        ('hr', '👥 Ressources Humaines'),
        ('quality', '📊 Qualité'),
        ('risk', '⚠️ Risque'),
    ], string='Catégorie', default='operational')

    formula_expression = fields.Char(
        string='Expression de calcul',
        required=True,
        help="Expression Python pour le calcul"
    )

    formula_fields = fields.Char(
        string='Champs nécessaires',
        help="Champs requis pour le calcul (séparés par des virgules)"
    )

    unit = fields.Char(string='Unité', default='%')
    measure_unit = fields.Selection([
        ('number', 'Nombre'),
        ('percentage', 'Pourcentage (%)'),
        ('amount', 'Montant (FCFA)'),
        ('days', 'Jours'),
        ('hours', 'Heures'),
        ('rate', 'Taux'),
    ], string='Unité de mesure', default='percentage')

    sample_parameters = fields.Text(
        string='Paramètres d\'exemple',
        help="Exemple de paramètres pour tester la formule (format JSON)",
        default='{"errors": 5, "total": 100}'
    )

    expected_result = fields.Float(
        string='Résultat attendu',
        help="Résultat attendu avec les paramètres d'exemple"
    )

    active = fields.Boolean(default=True)

    def action_apply_template(self):
        """Applique le modèle à un KRI existant"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': f'Appliquer le modèle - {self.name}',
            'res_model': 'risk.kri.formula.apply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_template_id': self.id,
                'default_formula_expression': self.formula_expression,
                'default_formula_fields': self.formula_fields,
                'default_unit': self.unit,
                'default_measure_unit': self.measure_unit,
                'default_sample_parameters': self.sample_parameters,
                'default_expected_result': self.expected_result,
            },
        }


class RiskKriFormulaTestWizard(models.TransientModel):
    _name = 'risk.kri.formula.test.wizard'
    _description = 'Assistant de test de formule'

    formula_expression = fields.Char(
        string='Expression de calcul',
        required=True,
        help="Expression Python à tester"
    )

    formula_fields = fields.Char(
        string='Champs nécessaires',
        help="Champs requis pour le calcul (séparés par des virgules)"
    )

    parameter_ids = fields.One2many(
        'risk.kri.formula.test.parameter',
        'wizard_id',
        string='Paramètres de test'
    )

    test_result = fields.Float(
        string='Résultat du test',
        readonly=True
    )

    test_success = fields.Boolean(
        string='Test réussi',
        readonly=True
    )

    test_message = fields.Text(
        string='Message du test',
        readonly=True
    )

    execution_time = fields.Float(
        string='Temps d\'exécution (ms)',
        readonly=True
    )

    @api.onchange('formula_fields')
    def _onchange_formula_fields(self):
        """Met à jour les paramètres quand les champs changent"""
        if self.formula_fields:
            fields_list = [f.strip() for f in self.formula_fields.split(',')]
            existing_names = self.parameter_ids.mapped('name')

            for field_name in fields_list:
                if field_name and field_name not in existing_names:
                    self.parameter_ids = [(0, 0, {'name': field_name})]

    def action_test_formula(self):
        """Exécute le test de la formule"""
        self.ensure_one()

        import time
        start_time = time.time()

        try:
            params = {}
            for param in self.parameter_ids:
                params[param.name] = param.value

            safe_dict = {
                'abs': abs,
                'round': round,
                'sum': sum,
                'len': len,
                'max': max,
                'min': min,
                'float': float,
                'int': int,
                'str': str,
            }
            safe_dict.update(params)

            result = eval(self.formula_expression, {"__builtins__": {}}, safe_dict)
            self.test_result = float(result)
            self.test_success = True
            self.test_message = "✅ Test réussi !"

        except Exception as e:
            self.test_result = 0
            self.test_success = False
            self.test_message = f"❌ Erreur: {str(e)}"

        finally:
            self.execution_time = round((time.time() - start_time) * 1000, 2)

        # ⚠️ Sans ce retour explicite, Odoo referme la fenêtre modale après l'appel
        # du bouton (aucune action de suite = fermeture par défaut). On rouvre donc
        # le même assistant, rafraîchi avec le résultat du test.
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class RiskKriFormulaTestParameter(models.TransientModel):
    _name = 'risk.kri.formula.test.parameter'
    _description = 'Paramètre de test de formule'

    wizard_id = fields.Many2one(
        'risk.kri.formula.test.wizard',
        string='Assistant',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        string='Nom du paramètre',
        required=True
    )

    value = fields.Float(
        string='Valeur',
        required=True,
        default=0
    )

    description = fields.Char(
        string='Description'
    )


class RiskKriFormulaApplyWizard(models.TransientModel):
    _name = 'risk.kri.formula.apply.wizard'
    _description = 'Assistant d\'application de formule'

    template_id = fields.Many2one(
        'risk.kri.formula.template',
        string='Modèle de formule'
    )

    kri_id = fields.Many2one(
        'risk.kri',
        string='KRI cible',
        required=True
    )

    formula_expression = fields.Char(
        string='Expression de calcul',
        required=True
    )

    formula_fields = fields.Char(
        string='Champs nécessaires'
    )

    unit = fields.Char(string='Unité', default='%')
    measure_unit = fields.Selection([
        ('number', 'Nombre'),
        ('percentage', 'Pourcentage (%)'),
        ('amount', 'Montant (FCFA)'),
        ('days', 'Jours'),
        ('hours', 'Heures'),
        ('rate', 'Taux'),
    ], string='Unité de mesure', default='percentage')

    sample_parameters = fields.Text(
        string='Paramètres d\'exemple'
    )

    expected_result = fields.Float(
        string='Résultat attendu'
    )

    apply_to_thresholds = fields.Boolean(
        string='Appliquer les seuils du modèle',
        default=True
    )

    threshold_green = fields.Float(string='🟢 Seuil Vert', default=0)
    threshold_amber = fields.Float(string='🟡 Seuil Orange', default=50)
    threshold_red = fields.Float(string='🔴 Seuil Rouge', default=80)

    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            self.formula_expression = self.template_id.formula_expression
            self.formula_fields = self.template_id.formula_fields
            self.unit = self.template_id.unit
            self.measure_unit = self.template_id.measure_unit
            self.sample_parameters = self.template_id.sample_parameters
            self.expected_result = self.template_id.expected_result

    def action_apply(self):
        """Applique la formule au KRI"""
        self.ensure_one()

        vals = {
            'formula_expression': self.formula_expression,
            'formula_fields': self.formula_fields,
            'unit': self.unit,
            'measure_unit': self.measure_unit,
        }

        if self.apply_to_thresholds:
            vals.update({
                'threshold_green': self.threshold_green,
                'threshold_amber': self.threshold_amber,
                'threshold_red': self.threshold_red,
            })

        self.kri_id.write(vals)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Formule appliquée',
            'res_model': 'risk.kri',
            'view_mode': 'form',
            'res_id': self.kri_id.id,
            'target': 'current',
        }