import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


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

    formula_version = fields.Integer(
        related='kri_id.formula_version',
        readonly=True,
        string='Version de la formule'
    )

    @api.onchange('kri_id')
    def _onchange_kri_id(self):
        if self.kri_id:
            self.formula_expression = self.kri_id.formula_expression
            self.formula_fields = self.kri_id.formula_fields

            if self.formula_fields:
                # ✅ Filtre les jetons vides (ex. "returns, total," avec une
                # virgule finale, ou "returns,,total") : sans ce filtre, un tel
                # jeton créait une ligne de paramètre avec un nom vide, qui
                # échouait ensuite avec "Nom du paramètre manquant" au moment
                # de calculer/enregistrer, sans qu'aucune ligne visible
                # n'explique l'erreur.
                fields_list = [
                    f.strip() for f in self.formula_fields.split(',') if f.strip()
                ]
                for field_name in fields_list:
                    if not self.parameter_ids.filtered(lambda p: p.name == field_name):
                        self.parameter_ids = [(0, 0, {'name': field_name})]

    @api.model_create_multi
    def create(self, vals_list):
        """Garantit la création des lignes de paramètres côté serveur.

        L'onchange _onchange_kri_id ci-dessus ne se déclenche, à l'ouverture
        de cet assistant, qu'à cause de la valeur par défaut du contexte
        (default_kri_id) — pas d'une vraie saisie utilisateur. Dans ce cas,
        les lignes de parameter_ids qu'il crée restent, pour une raison liée
        au client web, absentes de l'enregistrement réel du wizard
        (parameter_ids=[] constaté par logs au moment du calcul, alors que le
        tableau affiché dans le navigateur montrait bien une ligne). Pour ne
        plus dépendre de ce mécanisme fragile, les lignes sont recréées ici
        explicitement, juste après la création du wizard, à partir de
        formula_fields — qui, lui, est bien présent (transmis via
        default_formula_fields)."""
        records = super().create(vals_list)
        for record in records:
            if not record.formula_fields:
                continue
            fields_list = [
                f.strip() for f in record.formula_fields.split(',') if f.strip()
            ]
            existing_names = set(record.parameter_ids.mapped('name'))
            for field_name in fields_list:
                if field_name not in existing_names:
                    self.env['risk.kri.compute.parameter'].create({
                        'wizard_id': record.id,
                        'name': field_name,
                        'value': 0.0,
                    })
                    existing_names.add(field_name)
        return records

    def action_compute(self):
        """Calcule la valeur à partir des paramètres saisis"""
        self.ensure_one()

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

            formula_expression = self.env['risk.kri']._normalize_formula_expression(self.formula_expression)
            result = eval(formula_expression, {"__builtins__": {}}, safe_dict)
            self.computed_value = float(result)

        except Exception as e:
            raise ValidationError(_("Erreur de calcul: %s") % str(e))

        # ⚠️ Sans ce retour explicite, Odoo referme la fenêtre modale après
        # l'appel du bouton (aucune action de suite = fermeture par défaut,
        # constaté : le popup disparaissait et rien ne s'affichait après un
        # calcul pourtant réussi). On rouvre donc le même assistant, rafraîchi
        # avec la valeur calculée — même pattern que action_test_formula sur
        # risk.kri.formula.test.wizard.
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_save_measure(self):
        """Enregistre la mesure calculée.

        Recalcule systématiquement à partir des paramètres actuellement
        saisis juste avant l'enregistrement (au lieu de se fier à un
        computed_value potentiellement obsolète) : garantit que la mesure
        sauvegardée correspond toujours à la dernière valeur des paramètres,
        même si l'utilisateur a modifié un paramètre après avoir cliqué sur
        "Calculer", ou n'a jamais cliqué dessus. Ceci corrige aussi un bug où
        le contrôle précédent ("if self.computed_value is None") ne se
        déclenchait jamais, computed_value valant 0.0 par défaut (jamais
        None) sur un champ Float."""
        self.ensure_one()

        self.action_compute()

        # Créer la mesure avec la version de la formule. Contexte de
        # contournement nécessaire : risk.kri.measure refuse toute mesure
        # saisie manuellement pour un KRI ayant une formule définie ; cet
        # assistant EST le chemin légitime de calcul via cette formule.
        self.env['risk.kri.measure'].with_context(kri_formula_bypass=True).create({
            'kri_id': self.kri_id.id,
            'value': self.computed_value,
            'measure_date': self.measure_date,
            'comment': self.comment or f"Calcul automatique le {fields.Date.today()}",
            'formula_version': self.formula_version,
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

    @api.model_create_multi
    def create(self, vals_list):
        """Filtre défensivement toute ligne sans nom de paramètre exploitable
        (nom absent, vide, ou uniquement des espaces) avant l'écriture en
        base, au lieu de laisser échouer TOUT l'enregistrement de l'assistant
        de calcul avec une erreur de contrainte SQL peu explicite
        ("Missing required value for the field 'Nom du paramètre'"). Une
        ligne de paramètre sans nom ne peut de toute façon jamais correspondre
        à une variable réelle de la formule : mieux vaut l'ignorer
        silencieusement que de bloquer tout le calcul de la mesure."""
        vals_list = [
            vals for vals in vals_list
            if (vals.get('name') or '').strip()
        ]
        if not vals_list:
            return self.browse()
        return super().create(vals_list)