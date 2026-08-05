# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class RiskKri(models.Model):
    _name = 'risk.kri'
    _description = 'Indicateur Clé de Risque'
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
        store=False,
        help="Sous-processus concerné",
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
    # FORMULE DE CALCUL AVEC HISTORISATION
    # ============================================================

    formula = fields.Text(
        string="Méthode de calcul",
        help="Formule de calcul du KRI",
        tracking=True
    )

    formula_expression = fields.Char(
        string="Expression de calcul",
        help="Expression Python pour le calcul",
        tracking=True
    )

    formula_fields = fields.Char(
        string="Champs nécessaires",
        help="Champs requis pour le calcul (séparés par des virgules)",
        tracking=True
    )

    # Historique des formules
    formula_history_ids = fields.One2many(
        'risk.kri.formula.history',
        'kri_id',
        string='Historique des formules'
    )

    formula_version = fields.Integer(
        string='Version de la formule',
        default=1,
        tracking=True
    )

    formula_last_modified = fields.Datetime(
        string='Dernière modification de la formule',
        readonly=True
    )

    formula_last_modified_by = fields.Many2one(
        'res.users',
        string='Dernière modification par',
        readonly=True
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

    threshold_green = fields.Float(
        string='🟢 Seuil Vert (OK)',
        default=0,
        help="Valeur en dessous de laquelle le KRI est vert",
        tracking=True
    )

    threshold_amber = fields.Float(
        string='🟡 Seuil Orange (Alerte)',
        default=50,
        help="Valeur à partir de laquelle le KRI passe en alerte orange",
        tracking=True
    )

    threshold_red = fields.Float(
        string='🔴 Seuil Rouge (Critique)',
        default=80,
        help="Valeur à partir de laquelle le KRI passe en alerte rouge",
        tracking=True
    )

    threshold_appetite = fields.Float(
        string="🎯 Seuil d'appétit",
        default=80,
        help="Seuil de tolérance au risque pour ce KRI, indépendant des seuils "
             "vert/orange/rouge de pilotage opérationnel : au-delà, le KRI est "
             "considéré hors appétit au risque (vision comité des risques / "
             "gouvernance), même si le pilotage courant reste sur les seuils "
             "vert/orange/rouge. À définir explicitement par KRI, pas déduit du "
             "seuil rouge.",
        tracking=True
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

    over_appetite = fields.Boolean(
        compute='_compute_over_appetite',
        store=True,
        string='Hors appétit',
        help="Vrai si la valeur actuelle dépasse le seuil d'appétit défini pour ce KRI "
             "(indépendant du statut vert/orange/rouge de pilotage opérationnel)."
    )

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

    action_plan = fields.Html(
        string="Plan d'action",
        help="Plan d'action en cas d'alerte ou de dépassement des seuils"
    )

    notes = fields.Text(
        string='Notes',
        help="Notes et commentaires supplémentaires"
    )

    # ============================================================
    # HIÉRARCHIE GRC
    # ============================================================

    macro_process_id = fields.Many2one(
        'risk.macro.process',
        compute='_compute_hierarchy_fields',
        store=True,
        string='Macro-processus',
        help="Macro-processus déduit des risques associés"
    )

    process_id = fields.Many2one(
        'risk.process',
        compute='_compute_hierarchy_fields',
        store=True,
        string='Processus',
        help="Processus déduit des risques associés"
    )

    activity_id = fields.Many2one(
        'risk.activity',
        compute='_compute_hierarchy_fields',
        store=True,
        string='Activité',
        help="Activité déduite des risques associés"
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
    # PROCESSUS ET ACTIVITÉS (via les risques)
    # ============================================================

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

    macro_process_list = fields.Text(
        compute='_compute_process_list',
        string='Macro-processus',
        store=False,
        help='Liste des macro-processus des risques associés'
    )

    risk_count = fields.Integer(
        compute='_compute_risk_count',
        string='Nombre de risques liés',
        store=True
    )

    # ============================================================
    # SURCHARGE DE WRITE POUR HISTORISER LES FORMULES
    # ============================================================

    def write(self, vals):
        """Surcharge pour historiser les modifications de formule"""
        formula_changed = False
        formula_fields = ['formula', 'formula_expression', 'formula_fields']

        for record in self:
            for field in formula_fields:
                if field in vals and vals[field] != getattr(record, field):
                    formula_changed = True
                    break

        result = super().write(vals)

        if formula_changed:
            for record in self:
                record._create_formula_history()

        return result

    def _create_formula_history(self):
        """Crée un enregistrement d'historique pour la formule actuelle"""
        self.ensure_one()

        self.env['risk.kri.formula.history'].create({
            'kri_id': self.id,
            'formula': self.formula,
            'formula_expression': self.formula_expression,
            'formula_fields': self.formula_fields,
            'formula_version': self.formula_version,
            'tolerance': self.tolerance,
            'threshold_green': self.threshold_green,
            'threshold_amber': self.threshold_amber,
            'threshold_red': self.threshold_red,
            'measure_frequency': self.measure_frequency,
            'created_by': self.env.user.id,
        })

        self.formula_version += 1
        self.formula_last_modified = fields.Datetime.now()
        self.formula_last_modified_by = self.env.user

    def action_view_formula_history(self):
        """Ouvre la vue de l'historique des formules"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Historique des formules - {self.name}',
            'res_model': 'risk.kri.formula.history',
            'view_mode': 'list,form',
            'domain': [('kri_id', '=', self.id)],
            'context': {'default_kri_id': self.id},
            'target': 'current',
        }

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

    @api.depends('current_value', 'threshold_green', 'threshold_amber', 'threshold_red')
    def _compute_status(self):
        """
        Calcule le statut à partir des seuils réellement configurés et visibles
        dans le formulaire (threshold_green/amber/red), en détectant automatiquement
        le sens de l'échelle à partir de leur ordre :
        - Si le seuil rouge est supérieur au seuil orange : échelle croissante
          (plus la valeur est haute, plus c'est grave — ex: taux d'incidents).
        - Sinon : échelle décroissante (plus la valeur est basse, plus c'est
          grave — ex: taux de transformation, où l'on veut une valeur haute).
        """
        for record in self:
            value = record.current_value
            green = record.threshold_green
            amber = record.threshold_amber
            red = record.threshold_red

            if red >= amber:
                # Échelle croissante
                if value >= red:
                    record.status = 'red'
                elif value >= amber:
                    record.status = 'amber'
                else:
                    record.status = 'green'
            else:
                # Échelle décroissante
                if value <= red:
                    record.status = 'red'
                elif value <= amber:
                    record.status = 'amber'
                else:
                    record.status = 'green'

    @api.depends('current_value', 'threshold_appetite', 'threshold_amber', 'threshold_red')
    def _compute_over_appetite(self):
        """
        Réutilise la même détection de sens d'échelle que _compute_status
        (à partir de l'ordre seuil rouge / seuil orange), mais compare la
        valeur actuelle au seuil d'appétit — distinct du seuil rouge — pour
        déterminer si ce KRI est hors appétit au risque.
        """
        for record in self:
            increasing_scale = record.threshold_red >= record.threshold_amber
            if increasing_scale:
                record.over_appetite = record.current_value >= record.threshold_appetite
            else:
                record.over_appetite = record.current_value <= record.threshold_appetite

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

    @api.depends(
        'risk_ids', 'risk_ids.activity_id', 'risk_ids.activity_id.process_id',
        'risk_ids.activity_id.process_id.macro_process_id', 'risk_ids.process_id',
        'risk_ids.process_id.macro_process_id', 'risk_ids.macro_process_id',
    )
    def _compute_process_list(self):
        for record in self:
            processes = set()
            activities = set()
            macro_processes = set()

            for risk in record.risk_ids:
                if risk.activity_id:
                    if risk.activity_id.name:
                        activities.add(risk.activity_id.name)
                    if risk.activity_id.process_id and risk.activity_id.process_id.name:
                        processes.add(risk.activity_id.process_id.name)
                        if risk.activity_id.process_id.macro_process_id and risk.activity_id.process_id.macro_process_id.name:
                            macro_processes.add(risk.activity_id.process_id.macro_process_id.name)
                if risk.process_id and risk.process_id.name:
                    processes.add(risk.process_id.name)
                    if risk.process_id.macro_process_id and risk.process_id.macro_process_id.name:
                        macro_processes.add(risk.process_id.macro_process_id.name)
                if risk.macro_process_id and risk.macro_process_id.name:
                    macro_processes.add(risk.macro_process_id.name)

            record.process_list = ', '.join(sorted(processes)) if processes else ''
            record.activity_list = ', '.join(sorted(activities)) if activities else ''
            record.macro_process_list = ', '.join(sorted(macro_processes)) if macro_processes else ''

    @api.depends('risk_ids')
    def _compute_risk_count(self):
        for record in self:
            record.risk_count = len(record.risk_ids)

    @api.depends('risk_ids', 'risk_ids.activity_id', 'risk_ids.process_id', 'risk_ids.macro_process_id')
    def _compute_hierarchy_fields(self):
        for record in self:
            record.macro_process_id = False
            record.process_id = False
            record.activity_id = False

            if not record.risk_ids:
                continue

            for risk in record.risk_ids:
                if risk.activity_id:
                    record.activity_id = risk.activity_id.id
                    if risk.activity_id.process_id:
                        record.process_id = risk.activity_id.process_id.id
                        if risk.activity_id.process_id.macro_process_id:
                            record.macro_process_id = risk.activity_id.process_id.macro_process_id.id
                            break
                elif risk.process_id:
                    record.process_id = risk.process_id.id
                    if risk.process_id.macro_process_id:
                        record.macro_process_id = risk.process_id.macro_process_id.id
                        break
                elif risk.macro_process_id:
                    record.macro_process_id = risk.macro_process_id.id
                    break

    # ============================================================
    # CALCUL AUTOMATIQUE
    # ============================================================

    def compute_value_from_formula(self, **kwargs):
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
        self.ensure_one()

        value = self.compute_value_from_formula(**kwargs)

        measure = self.env['risk.kri.measure'].create({
            'kri_id': self.id,
            'value': value,
            'measure_date': fields.Date.today(),
            'comment': f"Calcul automatique le {fields.Date.today()}",
            'formula_version': self.formula_version,
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
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configurer les seuils',
            'res_model': 'risk.kri.threshold.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_kri_id': self.id},
        }

    def action_recalculate_hierarchy(self):
        kris = self.search([])
        count = 0
        for kri in kris:
            kri._compute_hierarchy_fields()
            count += 1

        return {
            'type': 'ir.actions.act_window',
            'name': 'Recalcul terminé',
            'res_model': 'risk.kri',
            'view_mode': 'list',
            'target': 'new',
            'context': {
                'default_name': f'{count} KRI recalculés'
            }
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
                    'formula_version': kri.formula_version,
                })

                _logger.info(f"KRI {kri.code} calculé: {value}")

            except Exception as e:
                _logger.error(f"Erreur pour KRI {kri.code}: {str(e)}")

    def action_test_formula(self):
        """Ouvre l'assistant de test de formule"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': '🧪 Tester la formule',
            'res_model': 'risk.kri.formula.test.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_formula_expression': self.formula_expression,
                'default_formula_fields': self.formula_fields,
            },
        }

    def action_apply_formula_template(self):
        """Ouvre l'assistant d'application de modèle de formule"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': '📋 Appliquer un modèle de formule',
            'res_model': 'risk.kri.formula.apply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_kri_id': self.id,
            },
        }


# ============================================================
# MODÈLE D'HISTORIQUE DES FORMULES
# ============================================================

class RiskKriFormulaHistory(models.Model):
    _name = 'risk.kri.formula.history'
    _description = 'Historique des formules KRI'
    _order = 'create_date desc, id desc'

    kri_id = fields.Many2one(
        'risk.kri',
        string='KRI',
        required=True,
        ondelete='cascade'
    )

    formula_version = fields.Integer(
        string='Version',
        help="Numéro de version de la formule"
    )

    formula = fields.Text(
        string='Méthode de calcul',
        help="Formule de calcul du KRI à cette version"
    )

    formula_expression = fields.Char(
        string='Expression de calcul',
        help="Expression Python pour le calcul"
    )

    formula_fields = fields.Char(
        string='Champs nécessaires',
        help="Champs requis pour le calcul"
    )

    tolerance = fields.Char(
        string='Tolérance',
        help="Valeur de tolérance"
    )

    threshold_green = fields.Float(
        string='🟢 Seuil Vert'
    )

    threshold_amber = fields.Float(
        string='🟡 Seuil Orange'
    )

    threshold_red = fields.Float(
        string='🔴 Seuil Rouge'
    )

    measure_frequency = fields.Selection([
        ('daily', 'Quotidienne'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('semiannual', 'Semestrielle'),
        ('annual', 'Annuelle'),
    ], string='Fréquence de capture')

    created_by = fields.Many2one(
        'res.users',
        string='Modifié par',
        default=lambda self: self.env.user
    )

    create_date = fields.Datetime(
        string='Date de modification',
        default=fields.Datetime.now
    )

    def action_restore_formula(self):
        """Restaure une version précédente de la formule"""
        self.ensure_one()

        self.kri_id.write({
            'formula': self.formula,
            'formula_expression': self.formula_expression,
            'formula_fields': self.formula_fields,
            'tolerance': self.tolerance,
            'threshold_green': self.threshold_green,
            'threshold_amber': self.threshold_amber,
            'threshold_red': self.threshold_red,
            'measure_frequency': self.measure_frequency,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Formule restaurée',
            'res_model': 'risk.kri',
            'view_mode': 'form',
            'res_id': self.kri_id.id,
            'target': 'current',
        }