# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RiskPriority(models.Model):
    _name = 'risk.priority'
    _description = 'Rang de priorité des risques'
    _order = 'sequence, level'
    _rec_name = 'name'

    level = fields.Integer(string='Niveau', required=True, help='Niveau de priorité (0 à 4)')
    sequence = fields.Integer(string='Séquence', default=10, help='Ordre d\'affichage')
    name = fields.Char(string='Nom', required=True, translate=True, help='Nom du rang de priorité')
    description = fields.Text(string='Description', translate=True, help='Description du rang de priorité')

    # Couleurs pour l'affichage
    color = fields.Char(string='Couleur', default='#6c757d',
                        help='Couleur associée au rang de priorité (hexadécimal)')
    badge_color = fields.Selection([
        ('success', 'Vert'),
        ('info', 'Bleu'),
        ('warning', 'Orange'),
        ('danger', 'Rouge'),
        ('secondary', 'Gris'),
        ('primary', 'Bleu foncé'),
    ], string='Couleur du badge', default='secondary', help='Couleur du badge pour l\'affichage')

    # Indicateurs
    is_urgent = fields.Boolean(string='Urgent', default=False, help='Indique si la priorité est urgente')
    is_critical = fields.Boolean(string='Critique', default=False, help='Indique si la priorité est critique')
    is_non_concerned = fields.Boolean(string='Non concerné', default=False,
                                      help='Indique si la priorité est "Non concerné"')

    active = fields.Boolean(string='Actif', default=True)

    # Statistiques
    risk_count = fields.Integer(compute='_compute_risk_count', store=True, string='Nombre de risques')

    @api.depends('risk_ids')
    def _compute_risk_count(self):
        for record in self:
            record.risk_count = len(record.risk_ids)

    # Relations
    risk_ids = fields.One2many('risk.risk', 'priority_id', string='Risques associés')

    _sql_constraints = [
        ('unique_level', 'unique(level)', 'Un niveau de priorité doit être unique !'),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.level}] {record.name}" if record.level is not None else record.name
            result.append((record.id, name))
        return result