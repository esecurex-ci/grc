from odoo import models, fields


class RiskKriMeasure(models.Model):
    _name = 'risk.kri.measure'
    _description = 'KRI Measure'
    _order = 'measure_date desc, id desc'

    kri_id = fields.Many2one(
        'risk.kri',
        string='KRI',
        required=True,
        ondelete='cascade'
    )

    measure_date = fields.Date(
        string='Date de mesure',
        required=True,
        default=fields.Date.today
    )

    value = fields.Float(
        string='Valeur',
        required=True
    )

    comment = fields.Html(
        string='Commentaire'
    )

    formula_version = fields.Integer(
        string='Version de la formule',
        help="Version de la formule utilisée pour ce calcul"
    )

    formula_history_id = fields.Many2one(
        'risk.kri.formula.history',
        string='Formule utilisée',
        help="Référence à la version de la formule utilisée"
    )

    parameters_used = fields.Text(
        string='Paramètres utilisés',
        help="Paramètres utilisés pour le calcul (format JSON)"
    )