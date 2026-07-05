from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskKriComputeWizard(models.TransientModel):
    _name = 'risk.kri.compute.wizard'
    _description = 'Assistant de calcul KRI'

    kri_id = fields.Many2one(
        'risk.kri',
        string='KRI',
        required=True,
        readonly=True
    )

    formula_expression = fields.Text(
        string='Formule',
        readonly=True
    )

    formula_fields = fields.Char(
        string='Champs nécessaires',
        readonly=True
    )

    parameter_ids = fields.One2many(
        'risk.kri.compute.parameter',
        'wizard_id',
        string='Paramètres'
    )

    computed_value = fields.Float(
        string='Valeur calculée',
        readonly=True
    )

    measure_date = fields.Date(
        string='Date de mesure',
        default=fields.Date.today,
        required=True
    )

    comment = fields.Text(
        string='Commentaire'
    )

    unit = fields.Char(
        string='Unité',
        related='kri_id.unit',
        readonly=True
    )

    measure_unit = fields.Selection(
        related='kri_id.measure_unit',
        readonly=True,
        string='Unité de mesure'
    )

    kri_name = fields.Char(
        related='kri_id.name',
        readonly=True,
        string='Nom du KRI'
    )

    kri_code = fields.Char(
        related='kri_id.code',
        readonly=True,
        string='Code KRI'
    )

    @api.onchange('kri_id')
    def _onchange_kri_id(self):
        if self.kri_id:
            self.formula_expression = self.kri_id.formula_expression
            self.formula_fields = self.kri_id.formula_fields

            # Créer les paramètres
            if self.formula_fields:
                fields_list = [f.strip() for f in self.formula_fields.split(',')]
                for field_name in fields_list:
                    if not self.parameter_ids.filtered(lambda p: p.name == field_name):
                        self.parameter_ids = [(0, 0, {'name': field_name})]

    def action_compute(self):
        """Calcule la valeur à partir des paramètres saisis"""
        self.ensure_one()

        # Récupérer les valeurs des paramètres
        params = {}
        for param in self.parameter_ids:
            params[param.name] = param.value

        try:
            safe_dict = {
                'abs': abs,
                'round': round,
                'sum': sum,
                'len': len,
                'max': max,
                'min': min,
            }
            safe_dict.update(params)

            result = eval(self.formula_expression, {"__builtins__": {}}, safe_dict)
            self.computed_value = float(result)

        except Exception as e:
            raise ValidationError(_("Erreur de calcul: %s") % str(e))

    def action_save_measure(self):
        """Enregistre la mesure calculée"""
        self.ensure_one()

        if self.computed_value is None:
            raise ValidationError(_("Veuillez d'abord calculer la valeur."))

        self.env['risk.kri.measure'].create({
            'kri_id': self.kri_id.id,
            'value': self.computed_value,
            'measure_date': self.measure_date,
            'comment': self.comment or f"Calcul automatique le {fields.Date.today()}",
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Mesure enregistrée',
            'res_model': 'risk.kri',
            'view_mode': 'form',
            'res_id': self.kri_id.id,
            'target': 'current',
        }


class RiskKriComputeParameter(models.TransientModel):
    _name = 'risk.kri.compute.parameter'
    _description = 'Paramètre de calcul KRI'

    wizard_id = fields.Many2one(
        'risk.kri.compute.wizard',
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
        required=True
    )

    description = fields.Char(
        string='Description'
    )