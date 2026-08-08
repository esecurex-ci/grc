from odoo import api, models, fields, _
from odoo.exceptions import ValidationError


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

    @api.constrains('value', 'kri_id')
    def _check_formula_required(self):
        """Un KRI qui a une formule de calcul définie (et testée via
        risk.kri.action_test_formula) DOIT voir toutes ses mesures produites
        par cette formule — via l'assistant 'Calculer la mesure'
        (risk.kri.compute.wizard) ou le calcul automatique planifié
        (risk.kri.cron) — jamais tapées à la main. Sans ce contrôle, la
        formule ne serait qu'une documentation sans effet : rien ne
        garantirait que la valeur enregistrée correspond réellement à ce que
        la formule est censée mesurer, ni ne permettrait de comparer deux
        mesures entre elles en confiance.

        Les chemins de calcul légitimes (assistant, cron, compute_and_save_
        measure) passent explicitement par
        with_context(kri_formula_bypass=True) pour contourner ce contrôle ;
        toute création/modification de mesure en dehors de ces chemins pour
        un KRI ayant une formule est refusée."""
        if self.env.context.get('kri_formula_bypass'):
            return
        for rec in self:
            if rec.kri_id.formula_expression:
                raise ValidationError(_(
                    "Le KRI « %s » a une formule de calcul définie : les "
                    "mesures ne peuvent pas être saisies manuellement pour ce "
                    "KRI. Utilisez le bouton « 🧮 Calculer la mesure » sur sa "
                    "fiche pour appliquer la formule."
                ) % rec.kri_id.name)