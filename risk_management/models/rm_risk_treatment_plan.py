from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class RiskTreatmentPlan(models.Model):
    _name = 'risk.treatment.plan'
    _description = 'Plan de traitement'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'target_date, name'

    # =====================================================
    # CHAMPS PRINCIPAUX
    # =====================================================

    name = fields.Char(
        string='Nom du plan',
        required=True,
        tracking=True
    )

    assessment_id = fields.Many2one(
        'risk.assessment',
        string='Évaluation',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    risk_id = fields.Many2one(
        'risk.risk',
        string='Risque',
        related='assessment_id.risk_id',
        store=True,
        readonly=True
    )

    # ✅ Correction : utiliser risk.function au lieu de hr.employee
    owner_id = fields.Many2one(
        'risk.function',
        string='Responsable',
        tracking=True
    )

    # ✅ Optionnel : garder un champ pour l'employé (information)
    owner_employee_id = fields.Many2one(
        'hr.employee',
        string='Employé',
        tracking=True
    )

    description = fields.Html(
        string='Description',
    )

    # =====================================================
    # DATES
    # =====================================================

    target_date = fields.Date(
        string='Date Cible',
        required=True,
        tracking=True
    )

    completion_date = fields.Date(
        string='Date de fin',
        readonly=True,
        tracking=True
    )

    # =====================================================
    # BUDGET
    # =====================================================

    budget = fields.Monetary(
        string='Budget',
        currency_field='currency_id',
        tracking=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id
    )

    code = fields.Char(
        string='Code',
        tracking=True,
        readonly=True,
        default='New',
        copy=False
    )

    # =====================================================
    # PROGRESS & STATE
    # =====================================================

    progress = fields.Float(
        string='Progression',
        default=0,
        tracking=True,
        help='Progress percentage (0-100)'
    )

    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('in_progress', 'En Progression'),
            ('completed', 'Clôturé'),
            ('cancelled', 'Annulé')
        ],
        string='Statut',
        default='draft',
        tracking=True
    )

    active = fields.Boolean(
        string='Active',
        default=True
    )

    # =====================================================
    # CHAMPS CALCULÉS
    # =====================================================

    is_overdue = fields.Boolean(
        compute='_compute_is_overdue',
        store=True,
        string='En retard'
    )

    days_remaining = fields.Integer(
        compute='_compute_is_overdue',
        store=True,
        string='Date restante'
    )

    notification_group_id = fields.Many2one(
        'res.groups',
        string='Groupe à notifier',
        default=lambda self: self.env.ref('risk_management.group_risk_manager', raise_if_not_found=False),
        help="Groupe d'utilisateurs qui recevront les notifications"
    )

    notification_user_ids = fields.Many2many(
        'res.users',
        string='Utilisateurs à notifier',
        help="Sélectionnez les utilisateurs qui recevront les notifications"
    )

    # =====================================================
    # CONSTRAINTS
    # =====================================================

    @api.constrains('progress')
    def _check_progress(self):
        for record in self:
            if record.progress < 0 or record.progress > 100:
                raise ValidationError(_("La progression doit être comprise entre 0 et 100."))

    @api.constrains('target_date', 'completion_date')
    def _check_dates(self):
        for record in self:
            if record.target_date and record.completion_date:
                if record.completion_date < record.target_date:
                    raise ValidationError(_("La date de fin ne peut pas être antérieure à la date cible."))

    # =====================================================
    # COMPUTE METHODS
    # =====================================================

    @api.depends('target_date', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            if record.target_date and record.state not in ['completed', 'cancelled']:
                record.is_overdue = record.target_date < today
                delta = (record.target_date - today).days
                record.days_remaining = max(0, delta)
            else:
                record.is_overdue = False
                record.days_remaining = 0

    # =====================================================
    # ACTION METHODS
    # =====================================================

    def action_reset_to_draft(self):
        """Remettre en brouillon"""
        for record in self:
            if record.state == 'cancelled':
                record.write({
                    'state': 'draft',
                    'progress': 0
                })

    def action_set_progress(self, value):
        """Définir la progression manuellement"""
        for record in self:
            if record.state == 'completed':
                raise ValidationError(_("Impossible de modifier la progression d'un plan terminé."))
            if 0 <= value <= 100:
                record.progress = value
                if value == 100:
                    record.action_complete()

    # =====================================================
    # AUTRES MÉTHODES
    # =====================================================

    def action_view_risk(self):
        """Voir le risque associé"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Risque',
            'res_model': 'risk.risk',
            'view_mode': 'form',
            'res_id': self.risk_id.id,
        }

    def action_view_assessment(self):
        """Voir l'évaluation associée"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Évaluation',
            'res_model': 'risk.assessment',
            'view_mode': 'form',
            'res_id': self.assessment_id.id,
        }

    # =====================================================
    # MÉTHODES DE NOTIFICATION
    # =====================================================

    def _get_users_to_notify(self):
        """Récupère les utilisateurs à notifier"""
        self.ensure_one()
        users = self.env['res.users']

        # 1. Le responsable réel du plan (priorité : employé assigné, puis fonction)
        if self.owner_employee_id and self.owner_employee_id.user_id:
            users |= self.owner_employee_id.user_id
        elif self.owner_id and hasattr(self.owner_id, 'user_id') and self.owner_id.user_id:
            users |= self.owner_id.user_id

        # 2. Utilisateurs sélectionnés manuellement
        if self.notification_user_ids:
            users |= self.notification_user_ids

        # 3. Groupe "Risk Manager" — uniquement si personne d'autre n'est identifié,
        #    pour éviter de notifier tous les risk managers de l'organisation
        #    à chaque plan de traitement, sans rapport avec leurs propres dossiers.
        if not users:
            risk_manager_group = self.env.ref('risk_management.group_risk_manager', raise_if_not_found=False)
            if risk_manager_group:
                manager_users = self.env['res.users'].search([
                    ('groups_id', 'in', risk_manager_group.id)
                ])
                users |= manager_users

        # 4. Si toujours personne, utiliser l'utilisateur courant
        if not users:
            users |= self.env.user

        return users

    def _create_notification_activity(self, user, summary, note, deadline=None):
        """Crée une activité de notification pour un utilisateur"""
        try:
            # Récupérer le type d'activité "À faire"
            activity_type = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
            if not activity_type:
                activity_type = self.env['mail.activity.type'].search([], limit=1)

            # ✅ CORRIGÉ : Gestion simple de la date
            if deadline:
                # Convertir en date Odoo
                if isinstance(deadline, str):
                    deadline = fields.Date.from_string(deadline)
                elif hasattr(deadline, 'date'):
                    deadline = deadline.date()
            else:
                deadline = fields.Date.today()

            self.activity_schedule(
                activity_type_id=activity_type.id,
                summary=summary,
                note=note,
                user_id=user.id,
                date_deadline=deadline
            )
            return True
        except Exception as e:
            _logger.error(f"Erreur lors de la création de l'activité pour {user.name}: {str(e)}")
            return False

    def notify_treatment_plan_created(self):
        """Notifie les utilisateurs concernés de la création d'un plan de traitement"""
        for record in self:
            try:
                users = record._get_users_to_notify()

                if not users:
                    _logger.warning(f"Aucun utilisateur à notifier pour le plan {record.name}")
                    continue

                summary = _("Nouveau plan de traitement créé")
                note = _("""
                    <b>Plan de traitement :</b> {plan_name}<br/>
                    <b>Risque :</b> {risk_name}<br/>
                    <b>Date cible :</b> {target_date}<br/>
                    <b>Description :</b> {description}<br/>
                    <br/>
                    Veuillez consulter le plan et prendre les actions nécessaires.
                """).format(
                    plan_name=record.name,
                    risk_name=record.risk_id.name if record.risk_id else 'Non spécifié',
                    target_date=record.target_date.strftime('%d/%m/%Y') if record.target_date else 'Non spécifiée',
                    description=record.description or 'Aucune description'
                )

                # ✅ CORRIGÉ : Utiliser fields.Date.to_date() pour la conversion
                if record.target_date:
                    deadline = fields.Date.to_date(record.target_date)
                else:
                    deadline = fields.Date.today()

                for user in users:
                    record._create_notification_activity(
                        user=user,
                        summary=summary,
                        note=note,
                        deadline=deadline
                    )

                # Message dans le chatter
                record.message_post(
                    body=_("""
                        <b>📢 Notification envoyée</b><br/>
                        <b>Destinataires :</b> {users}<br/>
                        <b>Plan de traitement :</b> {plan_name}
                    """).format(
                        users=', '.join(users.mapped('name')),
                        plan_name=record.name
                    ),
                    subtype_xmlid='mail.mt_note',
                )

            except Exception as e:
                _logger.error(f"Erreur lors de la notification pour {record.name}: {str(e)}")

    def notify_treatment_plan_updated(self):
        """Notifie les utilisateurs concernés des mises à jour du plan"""
        for record in self:
            try:
                users = record._get_users_to_notify()

                if not users:
                    continue

                summary = _("Plan de traitement mis à jour")
                note = _("""
                    <b>Plan de traitement :</b> {plan_name}<br/>
                    <b>Statut :</b> {state}<br/>
                    <b>Progression :</b> {progress}%<br/>
                    <b>Date cible :</b> {target_date}<br/>
                    <br/>
                    Veuillez consulter les mises à jour du plan.
                """).format(
                    plan_name=record.name,
                    state=dict(record._fields['state'].selection).get(record.state, record.state),
                    progress=record.progress,
                    target_date=record.target_date.strftime('%d/%m/%Y') if record.target_date else 'Non spécifiée'
                )

                # ✅ CORRIGÉ : Utiliser fields.Date.to_date()
                if record.target_date:
                    deadline = fields.Date.to_date(record.target_date)
                else:
                    deadline = fields.Date.today()

                for user in users:
                    record._create_notification_activity(
                        user=user,
                        summary=summary,
                        note=note,
                        deadline=deadline
                    )

            except Exception as e:
                _logger.error(f"Erreur lors de la notification de mise à jour pour {record.name}: {str(e)}")

    # =====================================================
    # SURCHARGE DES MÉTHODES CREATE ET WRITE
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Surcharge de create pour générer le code et notifier à la création"""
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.treatment.plan') or 'New'

        records = super().create(vals_list)

        # Notifier les utilisateurs concernés
        for record in records:
            record.notify_treatment_plan_created()

        return records

    def write(self, vals):
        """Surcharge de write pour notifier lors des mises à jour importantes"""
        # Vérifier si des champs importants sont modifiés
        important_fields = ['state', 'progress', 'target_date', 'name']
        should_notify = any(field in vals for field in important_fields)

        result = super().write(vals)

        if should_notify:
            for record in self:
                # Ne pas notifier si le plan est terminé ou annulé
                if record.state not in ['completed', 'cancelled']:
                    record.notify_treatment_plan_updated()

        return result

    # =====================================================
    # MÉTHODES D'ACTION EXISTANTES (modifiées)
    # =====================================================

    def action_start(self):
        """Démarrer le plan de traitement avec notification"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError("Seuls les plans en brouillon peuvent être démarrés.")

            record.write({
                'state': 'in_progress'
            })

            # Notifier le démarrage
            record.notify_treatment_plan_updated()

    def action_complete(self):
        """Terminer le plan de traitement"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError("Seuls les plans en cours peuvent être terminés.")

            record.write({
                'state': 'completed',
                'progress': 100,
                'completion_date': fields.Date.today()
            })

            # Notification spéciale de finalisation
            users = record._get_users_to_notify()
            if users:
                summary = _("✅ Plan de traitement terminé")
                note = _("""
                    <b>Plan de traitement :</b> {plan_name}<br/>
                    <b>Date de finalisation :</b> {completion_date}<br/>
                    <br/>
                    🎉 Le plan de traitement a été complété avec succès !
                """).format(
                    plan_name=record.name,
                    completion_date=fields.Date.today().strftime('%d/%m/%Y')
                )

                # ✅ CORRIGÉ : Utiliser fields.Date.to_date()
                deadline = fields.Date.to_date(fields.Date.today())

                for user in users:
                    record._create_notification_activity(
                        user=user,
                        summary=summary,
                        note=note,
                        deadline=deadline
                    )

    def action_cancel(self):
        """Annuler le plan de traitement"""
        for record in self:
            if record.state in ['completed', 'cancelled']:
                raise ValidationError("Les plans terminés ou annulés ne peuvent pas être annulés.")

            record.write({
                'state': 'cancelled'
            })

            # Notifier l'annulation
            record.notify_treatment_plan_updated()