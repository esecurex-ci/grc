# models/risk_process.py

from odoo import models, fields, api


class RiskProcess(models.Model):
    _name = 'risk.process'
    _description = 'Processus'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category, name'

    name = fields.Char(string='Nom du processus', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)

    category = fields.Selection([
        ('pilotage', 'Processus de Pilotage'),
        ('operational', 'Processus Opérationnels'),
        ('support', 'Processus Supports'),
    ], string='Catégorie', required=True, default='operational', tracking=True)

    macro_process_id = fields.Many2one('risk.macro.process', string='Famille', tracking=True)
    description = fields.Text(string='Description')
    owner_id = fields.Many2one('hr.employee', string='Propriétaire', tracking=True)
    active = fields.Boolean(default=True)

    # Relation inverse vers les risques
    risk_ids = fields.One2many('risk.risk', 'process_id', string='Risques associés')

    # ✅ Même échelle que risk.risk
    risk_level = fields.Selection([
        ('1', 'Très faible'),
        ('2', 'Faible'),
        ('3', 'Moyen'),
        ('4', 'Élevé'),
        ('5', 'Critique')
    ],
        compute='_compute_risk_stats',
        store=True,
        string='Niveau de risque')

    count_risk = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Nombre de risques"
    )

    @api.depends('risk_ids', 'risk_ids.risk_level', 'risk_ids.active')
    def _compute_risk_stats(self):
        for record in self:
            risks = record.risk_ids.filtered(lambda r: r.active)
            record.count_risk = len(risks)

            # Déterminer le niveau max (1-5)
            max_level = 1
            for risk in risks:
                level = int(risk.risk_level or 1)
                if level > max_level:
                    max_level = level
            record.risk_level = str(max_level)