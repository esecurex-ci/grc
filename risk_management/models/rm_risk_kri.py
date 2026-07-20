# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class RiskKri(models.Model):
    _name = 'risk.kri'
    _description = 'Key Risk Indicator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'status, name'

    # ============================================================
    # CHAMPS DE BASE
    # ============================================================

    name = fields.Char(string='Nom du KRI', required=True, tracking=True)
    code = fields.Char(string='Code', tracking=True)
    description = fields.Html(string='Description')

    category = fields.Selection([
        ('financial', '💰 Financier'),
        ('operational', '⚙️ Opérationnel'),
        ('compliance', '📋 Conformité'),
        ('strategic', '🎯 Stratégique'),
        ('cyber', '🔒 Cybersécurité'),
        ('reputation', '📢 Réputation'),
        ('accounting', '📊 Comptable'),
        ('administrative', '📋 Administratif'),
        ('hr', '👥 Ressources Humaines'),
    ], string='Catégorie', default='operational', tracking=True, index=True)

    # ============================================================
    # HIÉRARCHIE
    # ============================================================

    subprocess_id = fields.Many2one(
        'risk.subprocess',
        string='Sous-processus',
        tracking=True,
        help="Sous-processus concerné"
    )

    risk_generic_id = fields.Many2one(
        'risk.generic',
        string='Risque générique',
        tracking=True,
        help="Risque générique associé"
    )

    # ============================================================
    # INDICATEUR
    # ============================================================

    indicator_text = fields.Text(
        string="Indicateur du Risque",
        help="Description de l'indicateur"
    )

    measure_unit = fields.Selection([
        ('number', 'Nombre'),
        ('percentage', 'Pourcentage (%)'),
        ('amount', 'Montant (FCFA)'),
        ('days', 'Jours'),
        ('hours', 'Heures'),
        ('rate', 'Taux'),
    ], string='Unité de mesure', default='number', tracking=True)

    unit = fields.Char(
        string='Unité',
        help="Unité d'affichage (ex: %, FCFA, jours)",
        default='%'
    )

    # ============================================================
    # FORMULE DE CALCUL
    # ============================================================

    formula = fields.Text(
        string="Méthode de calcul",
        help="Formule de calcul du KRI"
    )

    formula_expression = fields.Char(
        string="Expression de calcul",
        help="Expression Python pour le calcul"
    )

    formula_fields = fields.Char(
        string="Champs nécessaires",
        help="Champs requis pour le calcul (séparés par des virgules)"
    )

    # ============================================================
    # SEUILS ET FRÉQUENCE
    # ============================================================

    measure_frequency = fields.Selection([
        ('daily', 'Quotidienne'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('semiannual', 'Semestrielle'),
        ('annual', 'Annuelle'),
    ], string='Fréquence de capture', default='monthly', tracking=True)

    tolerance = fields.Char(
        string='Tolérance',
        help="Valeur de tolérance (ex: <3, <2%)"
    )

    threshold_warning = fields.Float(
        string='Seuil d\'alerte',
        default=50,
        help="Seuil déclenchant une alerte"
    )

    threshold_critical = fields.Float(
        string='Seuil critique',
        default=80,
        help="Seuil déclenchant une alerte critique"
    )

    # ============================================================
    # VALEURS CALCULÉES
    # ============================================================

    current_value = fields.Float(
        compute='_compute_current_value',
        store=True,
        string='Valeur actuelle'
    )

    previous_value = fields.Float(
        compute='_compute_previous_value',
        store=True,
        string='Valeur précédente'
    )

    variation = fields.Float(
        compute='_compute_variation',
        store=True,
        string='Variation (%)',
        help="Variation en pourcentage entre la valeur actuelle et la précédente"
    )

    status = fields.Selection([
        ('green', '🟢 Vert'),
        ('amber', '🟡 Orange'),
        ('red', '🔴 Rouge')
    ], compute='_compute_status', store=True, string='Statut')

    trend = fields.Selection([
        ('up', '📈 En hausse'),
        ('down', '📉 En baisse'),
        ('stable', '➡️ Stable')
    ], compute='_compute_trend', store=True, string='Tendance')

    # ============================================================
    # MESURES - DATES
    # ============================================================

    measure_ids = fields.One2many(
        'risk.kri.measure',
        'kri_id',
        string='Mesures'
    )

    last_measure_date = fields.Date(
        compute='_compute_last_measure_date',
        store=True,
        string='Dernière mesure'
    )

    next_measure_date = fields.Date(
        compute='_compute_next_measure_date',
        store=True,
        string='Prochaine mesure',
        help="Date prévue pour la prochaine mesure"
    )

    overdue = fields.Boolean(
        compute='_compute_overdue',
        store=True,
        string='En retard',
        help="Indique si la mesure est en retard"
    )

    # ============================================================
    # ALERTES
    # ============================================================

    alert_count = fields.Integer(
        compute='_compute_alert_count',
        store=True,
        string="Nombre d'alertes",
        help="Nombre d'alertes générées pour ce KRI"
    )

    alert_ids = fields.One2many(
        'risk.kri.alert',
        'kri_id',
        string='Alertes'
    )

    last_alert_date = fields.Date(
        compute='_compute_last_alert_date',
        store=True,
        string='Dernière alerte'
    )

    # Dans votre modèle risk.kri
    threshold_green = fields.Float(
        string='Seuil Vert (OK)',
        default=0,
        help="Valeur en dessous de laquelle le KRI est vert"
    )

    threshold_amber = fields.Float(
        string='Seuil Orange (Alerte)',
        default=50,
        help="Valeur à partir de laquelle le KRI passe en alerte orange"
    )

    threshold_red = fields.Float(
        string='Seuil Rouge (Critique)',
        default=80,
        help="Valeur à partir de laquelle le KRI passe en alerte rouge"
    )

    action_plan = fields.Html(
        string="Plan d'action",
        help="Plan d'action en cas d'alerte ou de dépassement des seuils"
    )

    notes = fields.Text(
        string='Notes',
        help="Notes et commentaires supplémentaires"
    )

    # ============================================================
    # RELATIONS GRC
    # ============================================================

    risk_ids = fields.Many2many(
        'risk.risk',
        string='Risques associés'
    )

    owner_id = fields.Many2one(
        'hr.employee',
        string='Propriétaire',
        tracking=True
    )

    active = fields.Boolean(default=True)

    # ============================================================
    # PROCESSUS ET ACTIVITÉS (via les risques) - VERSION SIMPLIFIÉE
    # ============================================================

    # ✅ Uniquement des champs Text calculés, PAS de Many2many !
    process_list = fields.Text(
        compute='_compute_process_list',
        string='Processus',
        store=False,
        help='Liste des processus des risques associés'
    )

    activity_list = fields.Text(
        compute='_compute_process_list',
        string='Activités',
        store=False,
        help='Liste des activités des risques associés'
    )

    risk_count = fields.Integer(
        compute='_compute_risk_count',
        string='Nombre de risques liés',
        store=True
    )

    # ============================================================
    # COMPUTES
    # ============================================================

    @api.depends('measure_ids.value', 'measure_ids.measure_date')
    def _compute_current_value(self):
        for record in self:
            latest = record.measure_ids.sorted('measure_date', reverse=True)[:1]
            record.current_value = latest.value if latest else 0.0

    @api.depends('measure_ids.value', 'measure_ids.measure_date')
    def _compute_previous_value(self):
        for record in self:
            measures = record.measure_ids.sorted('measure_date', reverse=True)
            record.previous_value = measures[1].value if len(measures) >= 2 else 0.0

    @api.depends('current_value', 'previous_value')
    def _compute_variation(self):
        for record in self:
            if record.previous_value and record.previous_value != 0:
                variation = ((record.current_value - record.previous_value) / record.previous_value) * 100
                record.variation = round(variation, 1)
            else:
                record.variation = 0.0

    @api.depends('measure_ids.measure_date')
    def _compute_last_measure_date(self):
        for record in self:
            latest = record.measure_ids.sorted('measure_date', reverse=True)[:1]
            record.last_measure_date = latest.measure_date if latest else False

    @api.depends('last_measure_date', 'measure_frequency')
    def _compute_next_measure_date(self):
        for record in self:
            if not record.last_measure_date:
                record.next_measure_date = False
                continue

            delta = {
                'daily': relativedelta(days=1),
                'weekly': relativedelta(weeks=1),
                'monthly': relativedelta(months=1),
                'quarterly': relativedelta(months=3),
                'semiannual': relativedelta(months=6),
                'annual': relativedelta(years=1),
            }.get(record.measure_frequency, relativedelta(months=1))

            record.next_measure_date = record.last_measure_date + delta

    @api.depends('next_measure_date')
    def _compute_overdue(self):
        today = fields.Date.today()
        for record in self:
            record.overdue = bool(record.next_measure_date and record.next_measure_date < today)

    @api.depends('status')
    def _compute_alert_count(self):
        for record in self:
            record.alert_count = 1 if record.status in ['amber', 'red'] else 0

    @api.depends('alert_ids.create_date')
    def _compute_last_alert_date(self):
        for record in self:
            latest = record.alert_ids.sorted('create_date', reverse=True)[:1]
            record.last_alert_date = latest.create_date.date() if latest else False

    @api.depends('current_value', 'threshold_warning', 'threshold_critical')
    def _compute_status(self):
        for record in self:
            if record.current_value >= record.threshold_critical:
                record.status = 'red'
            elif record.current_value >= record.threshold_warning:
                record.status = 'amber'
            else:
                record.status = 'green'

    @api.depends('current_value', 'previous_value')
    def _compute_trend(self):
        for record in self:
            if record.previous_value == 0:
                record.trend = 'stable'
            elif record.current_value > record.previous_value:
                record.trend = 'up'
            elif record.current_value < record.previous_value:
                record.trend = 'down'
            else:
                record.trend = 'stable'

    @api.depends('risk_ids', 'risk_ids.activity_id', 'risk_ids.activity_id.process_id', 'risk_ids.process_id')
    def _compute_process_list(self):
        """Calcule la liste des processus et activités à partir des risques associés"""
        for record in self:
            processes = set()
            activities = set()

            for risk in record.risk_ids:
                # Via l'activité du risque
                if risk.activity_id:
                    if risk.activity_id.name:
                        activities.add(risk.activity_id.name)
                    if risk.activity_id.process_id and risk.activity_id.process_id.name:
                        processes.add(risk.activity_id.process_id.name)

                # Via le process_id direct du risque
                if risk.process_id and risk.process_id.name:
                    processes.add(risk.process_id.name)

            record.process_list = ', '.join(sorted(processes)) if processes else ''
            record.activity_list = ', '.join(sorted(activities)) if activities else ''

    @api.depends('risk_ids')
    def _compute_risk_count(self):
        for record in self:
            record.risk_count = len(record.risk_ids)

    # ============================================================
    # CALCUL AUTOMATIQUE
    # ============================================================

    def compute_value_from_formula(self, **kwargs):
        """
        Calcule la valeur du KRI à partir de la formule stockée.
        """
        self.ensure_one()

        if not self.formula_expression:
            raise ValidationError(_("Aucune formule définie pour ce KRI."))

        try:
            safe_dict = {
                'abs': abs,
                'round': round,
                'sum': sum,
                'len': len,
                'max': max,
                'min': min,
            }
            safe_dict.update(kwargs)

            result = eval(self.formula_expression, {"__builtins__": {}}, safe_dict)
            return float(result)
        except Exception as e:
            raise ValidationError(_("Erreur de calcul: %s") % str(e))

    def compute_and_save_measure(self, **kwargs):
        """
        Calcule la valeur et enregistre une mesure.
        """
        self.ensure_one()

        value = self.compute_value_from_formula(**kwargs)

        measure = self.env['risk.kri.measure'].create({
            'kri_id': self.id,
            'value': value,
            'measure_date': fields.Date.today(),
            'comment': f"Calcul automatique le {fields.Date.today()}",
        })

        return measure

    # ============================================================
    # MÉTHODES D'ACTION
    # ============================================================

    def action_add_measure(self):
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

    def action_compute_measure(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Calculer la mesure - {self.name}',
            'res_model': 'risk.kri.compute.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_kri_id': self.id,
                'default_formula_expression': self.formula_expression,
                'default_formula_fields': self.formula_fields,
            },
        }

    def action_view_measures(self):
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

    @api.model
    def _cron_compute_all_kris(self):
        """Cron pour calculer automatiquement tous les KRI"""
        kris = self.search([
            ('formula_expression', '!=', False),
            ('formula_expression', '!=', ''),
            ('active', '=', True)
        ])

        _logger.info(f"Calcul automatique pour {len(kris)} KRI")

        for kri in kris:
            try:
                params = {}
                fields_list = kri.formula_fields.split(',') if kri.formula_fields else []

                for field_name in fields_list:
                    field_name = field_name.strip()
                    params[field_name] = 0

                value = kri.compute_value_from_formula(**params)

                self.env['risk.kri.measure'].create({
                    'kri_id': kri.id,
                    'value': value,
                    'measure_date': fields.Date.today(),
                    'comment': f"Calcul automatique par cron le {fields.Date.today()}",
                })

                _logger.info(f"KRI {kri.code} calculé: {value}")

            except Exception as e:
                _logger.error(f"Erreur pour KRI {kri.code}: {str(e)}")