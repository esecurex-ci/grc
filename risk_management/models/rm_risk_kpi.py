from odoo import models, fields, api


class RiskKpi(models.Model):
    _name = 'risk.kpi'
    _description = 'Enterprise KPI'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    description = fields.Html()

    # ✅ NOUVEAU : Catégorie
    category = fields.Selection([
        ('financial', '💰 Financier'),
        ('operational', '⚙️ Opérationnel'),
        ('compliance', '📋 Conformité'),
        ('strategic', '🎯 Stratégique'),
    ], string='Catégorie', default='operational')

    owner_id = fields.Many2one('hr.employee', string='Propriétaire', tracking=True)
    unit = fields.Char(default='%')

    # ✅ NOUVEAU : Période
    period = fields.Selection([
        ('daily', 'Quotidienne'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('annual', 'Annuelle'),
    ], string='Période', default='monthly')

    # Valeurs
    target_value = fields.Float(string='Valeur cible', tracking=True)
    current_value = fields.Float(compute='_compute_current_value', store=True, string='Valeur actuelle')

    # ✅ NOUVEAU : Statut par rapport à la cible
    status = fields.Selection([
        ('exceeded', '✅ Dépassé'),
        ('on_target', '🎯 Sur cible'),
        ('below', '⚠️ En dessous'),
        ('critical', '🔴 Critique'),
    ], compute='_compute_status', store=True, string='Statut')

    # ✅ NOUVEAU : Progression
    progress = fields.Float(compute='_compute_progress', store=True, string='Progression (%)')

    measure_ids = fields.One2many('risk.kpi.measure', 'kpi_id', string='Mesures')
    last_measure_date = fields.Date(compute='_compute_last_measure_date', store=True)

    # ✅ NOUVEAU : Liens vers les risques
    risk_ids = fields.Many2many('risk.risk', string='Risques associés')

    # ============================================================
    # MÉTHODES DE CALCUL
    # ============================================================

    @api.depends('measure_ids.value', 'measure_ids.measure_date')
    def _compute_current_value(self):
        for rec in self:
            latest = rec.measure_ids.sorted('measure_date', reverse=True)[:1]
            rec.current_value = latest.value if latest else 0.0

    @api.depends('measure_ids.measure_date')
    def _compute_last_measure_date(self):
        for rec in self:
            latest = rec.measure_ids.sorted('measure_date', reverse=True)[:1]
            rec.last_measure_date = latest.measure_date if latest else False

    @api.depends('current_value', 'target_value')
    def _compute_status(self):
        for rec in self:
            if rec.target_value == 0:
                rec.status = 'on_target'
            elif rec.current_value >= rec.target_value:
                rec.status = 'exceeded'
            elif rec.current_value >= rec.target_value * 0.7:
                rec.status = 'on_target'
            elif rec.current_value >= rec.target_value * 0.5:
                rec.status = 'below'
            else:
                rec.status = 'critical'

    @api.depends('current_value', 'target_value')
    def _compute_progress(self):
        for rec in self:
            if rec.target_value and rec.target_value > 0:
                progress = (rec.current_value / rec.target_value) * 100
                rec.progress = min(progress, 100)
            else:
                rec.progress = 0

    # ============================================================
    # MÉTHODES D'ACTION
    # ============================================================

    def action_add_measure(self):
        """Ouvre la vue pour ajouter une mesure"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ajouter une mesure - {self.name}',
            'res_model': 'risk.kpi.measure',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_kpi_id': self.id,
                'default_measure_date': fields.Date.today(),
            },
        }

    def action_view_measures(self):
        """Ouvre la liste des mesures"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Mesures - {self.name}',
            'res_model': 'risk.kpi.measure',
            'view_mode': 'list,form,graph',
            'domain': [('kpi_id', '=', self.id)],
        }