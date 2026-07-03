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

    critical_risk_count = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Risques critiques"
    )

    high_risk_count = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Risques élevés"
    )

    medium_risk_count = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Risques moyens"
    )

    low_risk_count = fields.Integer(
        compute='_compute_risk_stats',
        store=True,
        string="Risques faibles"
    )

    activity_ids = fields.One2many(
        'risk.activity',
        'process_id',
        string='Activités'
    )

    activity_count = fields.Integer(
        compute='_compute_activity_count',
        store=True,
        string="Nombre d'activités"
    )

    activity_type_icon = fields.Char(
        compute='_compute_activity_type_icon',
        string='Icône',
        store=False
    )

    activity_summary = fields.Char(related='activity_ids.summary', string='Résumé')

    @api.depends('activity_ids')
    def _compute_activity_count(self):
        for record in self:
            record.activity_count = len(record.activity_ids)

    @api.depends('activity_ids', 'activity_ids.risk_ids', 'activity_ids.risk_ids.active')
    def _compute_risk_ids(self):
        """Récupère tous les risques des activités liées à ce processus"""
        for record in self:
            risks = record.activity_ids.mapped('risk_ids').filtered(lambda r: r.active)
            record.risk_ids = [(6, 0, risks.ids)]

    @api.depends('activity_ids', 'activity_ids.risk_ids', 'activity_ids.risk_ids.risk_level',
                 'activity_ids.risk_ids.active')
    def _compute_risk_stats(self):
        for record in self:
            risks = record.activity_ids.mapped('risk_ids').filtered(lambda r: r.active)

            record.count_risk = len(risks)
            record.critical_risk_count = len(risks.filtered(lambda r: r.risk_level == '5'))
            record.high_risk_count = len(risks.filtered(lambda r: r.risk_level == '4'))
            record.medium_risk_count = len(risks.filtered(lambda r: r.risk_level == '3'))
            record.low_risk_count = len(risks.filtered(lambda r: r.risk_level in ['1', '2']))

            max_level = 1
            for risk in risks:
                level = int(risk.risk_level or 1)
                if level > max_level:
                    max_level = level
            record.risk_level = str(max_level)

    def action_view_risks(self):
        """Ouvre la liste complète des risques associés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Risques - {self.name}',
            'res_model': 'risk.risk',
            'view_mode': 'list,form,kanban',
            'domain': [('activity_id.process_id', '=', self.id)],
            'context': {'default_process_id': self.id},
        }

    def action_add_risk(self):
        """Ouvre la vue de création d'un risque lié au processus"""
        self.ensure_one()
        activity = self.activity_ids[:1]
        if not activity:
            activity = self.env['risk.activity'].create({
                'name': f'Activité principale - {self.name}',
                'process_id': self.id,
                'owner_id': self.owner_id.id,
            })

        return {
            'type': 'ir.actions.act_window',
            'name': f'Ajouter un risque - {self.name}',
            'res_model': 'risk.risk',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_activity_id': activity.id,
                'default_process_id': self.id,
            },
        }

    def get_risk_stats(self):
        """Retourne les statistiques des risques associés"""
        self.ensure_one()
        risks = self.risk_ids.filtered(lambda r: r.active)
        return {
            'total': len(risks),
            'critical': len(risks.filtered(lambda r: r.risk_level == '5')),
            'high': len(risks.filtered(lambda r: r.risk_level == '4')),
            'medium': len(risks.filtered(lambda r: r.risk_level == '3')),
            'low': len(risks.filtered(lambda r: r.risk_level in ['1', '2'])),
        }

    def action_view_activities(self):
        """Ouvre la liste complète des activités du processus"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Activités - {self.name}',
            'res_model': 'risk.activity',
            'view_mode': 'list,form,kanban',
            'domain': [('process_id', '=', self.id)],
            'context': {'default_process_id': self.id},
        }

    def action_add_activity(self):
        """Ouvre la vue de création d'une activité liée au processus"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ajouter une activité - {self.name}',
            'res_model': 'risk.activity',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_process_id': self.id,
            },
        }

    @api.depends('category')
    def _compute_activity_type_icon(self):
        icons = {
            'pilotage': 'fa-flag',
            'operational': 'fa-cogs',
            'support': 'fa-life-ring',
        }
        for record in self:
            record.activity_type_icon = icons.get(record.category, 'fa-tasks')