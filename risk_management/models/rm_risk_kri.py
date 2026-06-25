from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta


class RiskKri(models.Model):
    _name = 'risk.kri'
    _description = 'Key Risk Indicator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'status, name'

    # Champs existants
    name = fields.Char(required=True, tracking=True)
    code = fields.Char(tracking=True)
    description = fields.Html()
    risk_ids = fields.Many2many('risk.risk', string='Risques associés')
    owner_id = fields.Many2one('hr.employee', string='Propriétaire', tracking=True)
    unit = fields.Char(default='%', tracking=True)

    # ✅ NOUVEAU : Catégorie d'indicateur
    category = fields.Selection([
        ('financial', '💰 Financier'),
        ('operational', '⚙️ Opérationnel'),
        ('compliance', '📋 Conformité'),
        ('strategic', '🎯 Stratégique'),
        ('cyber', '🔒 Cybersécurité'),
        ('reputation', '📢 Réputation'),
    ], string='Catégorie', default='operational', tracking=True)

    # ✅ NOUVEAU : Fréquence de mesure
    measure_frequency = fields.Selection([
        ('daily', 'Quotidienne'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('annual', 'Annuelle'),
    ], string='Fréquence', default='monthly', tracking=True)

    # ✅ NOUVEAU : Dates de suivi
    last_measure_date = fields.Date(
        compute='_compute_last_measure_date',
        store=True,
        string='Dernière mesure'
    )
    next_measure_date = fields.Date(
        compute='_compute_next_measure_date',
        store=True,
        string='Prochaine mesure'
    )
    overdue = fields.Boolean(
        compute='_compute_overdue',
        store=True,
        string='En retard'
    )

    # Seuils (existants)
    threshold_green = fields.Float(string='Seuil Vert (OK)', default=0, tracking=True)
    threshold_amber = fields.Float(string='Seuil Orange (Alerte)', default=50, tracking=True)
    threshold_red = fields.Float(string='Seuil Rouge (Critique)', default=80, tracking=True)

    # Valeurs calculées (existantes)
    current_value = fields.Float(compute='_compute_current_value', store=True)
    status = fields.Selection([
        ('green', '🟢 Vert'),
        ('amber', '🟡 Orange'),
        ('red', '🔴 Rouge')
    ], compute='_compute_status', store=True, string='Statut')

    # ✅ NOUVEAU : Tendance
    trend = fields.Selection([
        ('up', '📈 En hausse'),
        ('down', '📉 En baisse'),
        ('stable', '➡️ Stable')
    ], compute='_compute_trend', store=True, string='Tendance')

    # ✅ NOUVEAU : Valeur précédente
    previous_value = fields.Float(
        compute='_compute_previous_value',
        store=True,
        string='Valeur précédente'
    )

    # ✅ NOUVEAU : Variation
    variation = fields.Float(
        compute='_compute_variation',
        store=True,
        string='Variation (%)'
    )

    # Relations
    measure_ids = fields.One2many('risk.kri.measure', 'kri_id', string='Mesures')
    activity_id = fields.Many2one('risk.activity', string='Activité', ondelete='set null')
    process_id = fields.Many2one('risk.process', related='activity_id.process_id', store=True, string='Processus')

    # ✅ NOUVEAU : Alertes
    alert_ids = fields.One2many('risk.kri.alert', 'kri_id', string='Alertes')
    last_alert_date = fields.Date(compute='_compute_last_alert_date', store=True, string='Dernière alerte')
    alert_count = fields.Integer(compute='_compute_alert_count', store=True, string="Nombre d'alertes")

    # ✅ NOUVEAU : Commentaires et actions
    action_plan = fields.Html(string="Plan d'action en cas d'alerte")
    notes = fields.Text(string='Notes')

    # ============================================================
    # MÉTHODES DE CALCUL
    # ============================================================

    @api.depends('measure_ids.value', 'measure_ids.measure_date')
    def _compute_current_value(self):
        for rec in self:
            latest = rec.measure_ids.sorted('measure_date', reverse=True)[:1]
            rec.current_value = latest.value if latest else 0.0

    @api.depends('measure_ids.value', 'measure_ids.measure_date')
    def _compute_previous_value(self):
        for rec in self:
            measures = rec.measure_ids.sorted('measure_date', reverse=True)
            if len(measures) >= 2:
                rec.previous_value = measures[1].value
            else:
                rec.previous_value = 0.0

    @api.depends('current_value', 'previous_value')
    def _compute_variation(self):
        for rec in self:
            if rec.previous_value and rec.previous_value != 0:
                variation = ((rec.current_value - rec.previous_value) / rec.previous_value) * 100
                rec.variation = round(variation, 1)
            else:
                rec.variation = 0.0

    @api.depends('current_value', 'previous_value')
    def _compute_trend(self):
        for rec in self:
            if rec.previous_value == 0:
                rec.trend = 'stable'
            elif rec.current_value > rec.previous_value:
                rec.trend = 'up'
            elif rec.current_value < rec.previous_value:
                rec.trend = 'down'
            else:
                rec.trend = 'stable'

    @api.depends('current_value', 'threshold_green', 'threshold_amber', 'threshold_red')
    def _compute_status(self):
        for rec in self:
            if rec.current_value >= rec.threshold_red:
                rec.status = 'red'
            elif rec.current_value >= rec.threshold_amber:
                rec.status = 'amber'
            else:
                rec.status = 'green'

    @api.depends('measure_ids.measure_date')
    def _compute_last_measure_date(self):
        for rec in self:
            latest = rec.measure_ids.sorted('measure_date', reverse=True)[:1]
            rec.last_measure_date = latest.measure_date if latest else False

    @api.depends('last_measure_date', 'measure_frequency')
    def _compute_next_measure_date(self):
        for rec in self:
            if not rec.last_measure_date:
                rec.next_measure_date = False
                continue

            delta = {
                'daily': relativedelta(days=1),
                'weekly': relativedelta(weeks=1),
                'monthly': relativedelta(months=1),
                'quarterly': relativedelta(months=3),
                'annual': relativedelta(years=1),
            }.get(rec.measure_frequency, relativedelta(months=1))

            rec.next_measure_date = rec.last_measure_date + delta

    @api.depends('next_measure_date')
    def _compute_overdue(self):
        today = fields.Date.today()
        for rec in self:
            rec.overdue = bool(rec.next_measure_date and rec.next_measure_date < today)

    @api.depends('alert_ids.create_date')
    def _compute_last_alert_date(self):
        for rec in self:
            latest = rec.alert_ids.sorted('create_date', reverse=True)[:1]
            rec.last_alert_date = latest.create_date.date() if latest else False

    @api.depends('alert_ids')
    def _compute_alert_count(self):
        for rec in self:
            rec.alert_count = len(rec.alert_ids)

    # ============================================================
    # MÉTHODES D'ACTION
    # ============================================================

    def action_add_measure(self):
        """Ouvre la vue pour ajouter une mesure"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ajouter une mesure - {self.name}',
            'res_model': 'risk.kri.measure',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_kri_id': self.id,
                'default_measure_date': fields.Date.today(),
            },
        }

    def action_view_measures(self):
        """Ouvre la liste des mesures"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Mesures - {self.name}',
            'res_model': 'risk.kri.measure',
            'view_mode': 'list,form,graph',
            'domain': [('kri_id', '=', self.id)],
            'context': {'default_kri_id': self.id},
        }

    def action_generate_alert(self):
        """Génère une alerte pour ce KRI"""
        self.ensure_one()
        if self.status in ['amber', 'red']:
            self.env['risk.kri.alert'].create({
                'kri_id': self.id,
                'status': self.status,
                'value': self.current_value,
                'threshold': self.threshold_red if self.status == 'red' else self.threshold_amber,
                'message': f"⚠️ Alerte {self.status.upper()} - {self.name}: {self.current_value}{self.unit}",
            })

    def action_reset_thresholds(self):
        """Réinitialise les seuils aux valeurs par défaut"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configurer les seuils',
            'res_model': 'risk.kri.threshold.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_kri_id': self.id},
        }