from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class RiskKriCron(models.Model):
    _name = 'risk.kri.cron'
    _description = 'Planification du calcul KRI'

    def _compute_all_kris(self):
        """Calcule tous les KRI qui ont une formule définie"""
        kris = self.env['risk.kri'].search([
            ('formula_expression', '!=', False),
            ('formula_expression', '!=', ''),
        ])

        _logger.info(f"Calcul automatique pour {len(kris)} KRI")

        for kri in kris:
            try:
                # Ici, vous pouvez implémenter la logique pour récupérer
                # les valeurs des paramètres depuis d'autres modèles
                # Exemple : récupérer les données depuis risk.risk ou risk.incident

                # Pour l'instant, on fait un calcul simple avec des valeurs par défaut
                params = {}
                fields_list = kri.formula_fields.split(',') if kri.formula_fields else []

                for field_name in fields_list:
                    field_name = field_name.strip()
                    # Récupérer la valeur depuis les données (à adapter)
                    # Exemple : depuis les incidents
                    if field_name == 'incidents':
                        # Compter les incidents du mois
                        params[field_name] = self.env['risk.incident'].search_count([
                            ('create_date', '>=', fields.Date.today().replace(day=1)),
                            ('state', '=', 'validated')
                        ])
                    else:
                        # Valeur par défaut (à adapter)
                        params[field_name] = 0

                # Calculer la valeur
                value = kri.compute_value_from_formula(**params)

                # Créer la mesure
                self.env['risk.kri.measure'].create({
                    'kri_id': kri.id,
                    'value': value,
                    'measure_date': fields.Date.today(),
                    'comment': f"Calcul automatique par cron le {fields.Date.today()}",
                    'parameters': str(params),
                })

                _logger.info(f"KRI {kri.code} calculé: {value}")

            except Exception as e:
                _logger.error(f"Erreur pour KRI {kri.code}: {str(e)}")