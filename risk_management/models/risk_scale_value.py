from odoo import models, fields, api


class RiskScaleValue(models.Model):
    _name = 'risk.scale.value'
    _description = 'Valeur d\'échelle'
    _order = 'scale_type, sequence, value asc'

    name = fields.Char(string='Libellé', required=True, translate=True)

    # CHANGEMENT : value devient un Char pour accepter 'low', 'medium', etc.
    value = fields.Char(string='Valeur', required=True)

    # Pour les valeurs numériques (probabilité et impact)
    numeric_value = fields.Integer(string='Valeur numérique', help="Valeur numérique pour le calcul des scores")

    scale_type = fields.Selection([
        ('probability', 'Probabilité'),
        ('impact', 'Impact'),
        ('level', 'Niveau de risque')
    ], string='Type d\'échelle', required=True)

    color = fields.Char(string='Couleur', default='#6c757d')

    # Pour les niveaux de risque
    score_min = fields.Integer(string='Score minimum')
    score_max = fields.Integer(string='Score maximum')

    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    _sql_constraints = [
        ('unique_value_scale', 'unique(value, scale_type, company_id)',
         'Cette valeur existe déjà pour cette échelle.')
    ]

    @api.depends('value', 'name')
    def name_get(self):
        result = []
        for record in self:
            if record.scale_type == 'level':
                name = record.name
            else:
                name = f"{record.numeric_value or record.value} - {record.name}"
            result.append((record.id, name))
        return result