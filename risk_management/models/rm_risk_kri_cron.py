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
                params = {}
                fields_list = kri.formula_fields.split(',') if kri.formula_fields else []

                for field_name in fields_list:
                    field_name = field_name.strip()
                    # Récupérer la valeur depuis les données (à adapter selon vos besoins)
                    if field_name == 'incidents':
                        params[field_name] = self.env['risk.incident'].search_count([
                            ('create_date', '>=', fields.Date.today().replace(day=1)),
                        ])
                    elif field_name == 'errors':
                        params[field_name] = 0  # À remplacer par votre logique
                    elif field_name == 'total':
                        params[field_name] = 1  # À remplacer par votre logique
                    else:
                        params[field_name] = 0

                value = kri.compute_value_from_formula(**params)

                self.env['risk.kri.measure'].create({
                    'kri_id': kri.id,
                    'value': value,
                    'measure_date': fields.Date.today(),
                    'comment': f"Calcul automatique par cron le {fields.Date.today()}",
                    'formula_version': kri.formula_version,
                })

                _logger.info(f"KRI {kri.code} calculé: {value}")

                # ✅ Génération automatique d'une alerte si le KRI vient de passer
                # en orange/rouge — sans créer de doublon si une alerte du même
                # niveau est déjà ouverte (non résolue) pour ce KRI.
                if kri.status in ('amber', 'red'):
                    existing_open_alert = self.env['risk.kri.alert'].search([
                        ('kri_id', '=', kri.id),
                        ('resolved', '=', False),
                        ('status', '=', kri.status),
                    ], limit=1)

                    if not existing_open_alert:
                        kri.action_generate_alert()
                        _logger.info(f"Alerte {kri.status.upper()} générée automatiquement pour le KRI {kri.code}")

            except Exception as e:
                _logger.error(f"Erreur pour KRI {kri.code}: {str(e)}")