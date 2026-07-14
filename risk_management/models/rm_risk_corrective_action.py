from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class RiskCorrectiveAction(models.Model):
    _name = 'risk.corrective.action'
    _description = 'Action corrective / Plan d\'action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'deadline, state'
    _rec_name = 'name'

    # ============================================================
    # INFORMATIONS GÉNÉRALES
    # ============================================================

    name = fields.Char(
        string='Action',
        required=True,
        tracking=True
    )

    code = fields.Char(
        string='Code',
        tracking=True
    )

    description = fields.Html(
        string='Description'
    )

    action_type = fields.Selection([
        ('corrective', '🔧 Corrective'),
        ('preventive', '🛡️ Préventive'),
        ('improvement', '📈 Amélioration'),
    ], string='Type d\'action', default='corrective', required=True, tracking=True)

    # ============================================================
    # CONTEXTE
    # ============================================================

    incident_id = fields.Many2one(
        'risk.incident',
        string='Incident associé',
        tracking=True,
        ondelete='cascade'
    )

    risk_id = fields.Many2one(
        'risk.risk',
        string='Risque associé',
        tracking=True
    )

    control_id = fields.Many2one(
        'risk.control',
        string='Contrôle associé',
        tracking=True
    )

    control_test_id = fields.Many2one(
        'risk.control.test',
        string='Test associé',
        tracking=True
    )

    # ============================================================
    # RESPONSABLES
    # ============================================================

    owner_id = fields.Many2one(
        'hr.employee',
        string='Responsable',
        required=True,
        tracking=True
    )

    reviewer_id = fields.Many2one(
        'hr.employee',
        string='Relecteur',
        tracking=True
    )

    approver_id = fields.Many2one(
        'hr.employee',
        string='Approbateur',
        tracking=True
    )

    # ============================================================
    # PLANIFICATION
    # ============================================================

    deadline = fields.Date(
        string='Date limite',
        required=True,
        tracking=True
    )

    # ✅ ALIAS pour compatibilité (due_date → deadline)
    due_date = fields.Date(
        related='deadline',
        string='Date d\'échéance',
        store=True
    )

    start_date = fields.Date(
        string='Date de début',
        default=fields.Date.today,
        tracking=True
    )

    end_date = fields.Date(
        string='Date de fin',
        tracking=True
    )

    # ============================================================
    # RESSOURCES
    # ============================================================

    estimated_cost = fields.Float(
        string='Coût estimé',
        tracking=True
    )

    actual_cost = fields.Float(
        string='Coût réel',
        tracking=True
    )

    estimated_duration = fields.Float(
        string='Durée estimée (heures)',
        default=1
    )

    actual_duration = fields.Float(
        string='Durée réelle (heures)'
    )

    # ============================================================
    # AVANCEMENT
    # ============================================================

    progress = fields.Float(
        string='Progression (%)',
        default=0,
        digits=(16, 2),
        tracking=True
    )

    state = fields.Selection([
        ('draft', '📝 Brouillon'),
        ('in_progress', '🔄 En cours'),
        ('review', '🔍 En relecture'),
        ('done', '✅ Terminé'),
        ('overdue', '⏰ En retard'),
        ('cancelled', '❌ Annulé'),
    ], string='Statut', default='draft', tracking=True, index=True)

    # ============================================================
    # RÉSULTATS
    # ============================================================

    result = fields.Html(
        string='Résultat de l\'action'
    )

    closure_date = fields.Date(
        string='Date de clôture',
        tracking=True
    )

    # ============================================================
    # SUIVI
    # ============================================================

    follow_up_date = fields.Date(
        string='Date de suivi',
        tracking=True
    )

    follow_up_comment = fields.Html(
        string='Commentaire de suivi'
    )

    # ============================================================
    # NOTIFICATIONS
    # ============================================================

    notification_sent = fields.Boolean(
        string='Notification envoyée',
        default=False
    )

    reminder_sent = fields.Boolean(
        string='Rappel envoyé',
        default=False
    )

    # ============================================================
    # DOCUMENTS
    # ============================================================

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Pièces jointes'
    )

    # ============================================================
    # STATISTIQUES
    # ============================================================

    is_overdue = fields.Boolean(
        compute='_compute_is_overdue',
        string='En retard',
        store=True
    )

    days_remaining = fields.Integer(
        compute='_compute_days_remaining',
        string='Jours restants'
    )

    completion_rate = fields.Float(
        compute='_compute_completion_rate',
        string='Taux d\'achèvement (%)'
    )

    # ============================================================
    # COMPUTES
    # ============================================================

    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            if record.deadline and record.deadline < today and record.state not in ['done', 'cancelled']:
                record.is_overdue = True
                if record.state != 'overdue':
                    record.state = 'overdue'
            else:
                record.is_overdue = False

    @api.depends('deadline')
    def _compute_days_remaining(self):
        today = fields.Date.today()
        for record in self:
            if record.deadline:
                delta = record.deadline - today
                record.days_remaining = delta.days
            else:
                record.days_remaining = 0

    @api.depends('progress', 'state')
    def _compute_completion_rate(self):
        for record in self:
            if record.state == 'done':
                record.completion_rate = 100
            elif record.state in ['draft', 'cancelled']:
                record.completion_rate = 0
            else:
                record.completion_rate = record.progress

    # ============================================================
    # CONTRAINTES
    # ============================================================

    @api.constrains('deadline', 'start_date')
    def _check_dates(self):
        for record in self:
            if record.deadline and record.start_date and record.deadline < record.start_date:
                raise ValidationError(_("La date limite ne peut pas être antérieure à la date de début."))

    @api.constrains('progress')
    def _check_progress(self):
        for record in self:
            if record.progress < 0 or record.progress > 100:
                raise ValidationError(_("La progression doit être comprise entre 0 et 100%."))

    # ============================================================
    # MÉTHODES D'ACTION
    # ============================================================

    def action_start(self):
        """Démarrer l'action"""
        self.ensure_one()
        self.state = 'in_progress'
        self.start_date = fields.Date.today()
        self._send_notification('start')
        return True

    def action_review(self):
        """Soumettre à la revue"""
        self.ensure_one()
        self.state = 'review'
        self._send_notification('review')
        return True

    def action_done(self):
        """Terminer l'action"""
        self.ensure_one()
        self.state = 'done'
        self.progress = 100
        self.closure_date = fields.Date.today()
        return True

    def action_cancel(self):
        """Annuler l'action"""
        self.ensure_one()
        self.state = 'cancelled'
        return True

    def action_reset_to_draft(self):
        """Remettre en brouillon"""
        self.ensure_one()
        self.state = 'draft'
        return True

    def action_update_progress(self):
        """Ouvre l'assistant pour mettre à jour la progression"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mettre à jour la progression',
            'res_model': 'risk.action.progress.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_action_id': self.id},
        }

    def action_add_follow_up(self):
        """Ajouter un commentaire de suivi"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ajouter un suivi',
            'res_model': 'risk.action.followup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_action_id': self.id},
        }

    def _send_notification(self, notification_type):
        """Envoie une notification"""
        self.ensure_one()
        if self.owner_id and self.owner_id.user_id:
            self.message_post(
                body=f"""
                    <div style="font-family: Arial, sans-serif; padding: 10px;">
                        <h4>📋 Action: {self.name}</h4>
                        <p><strong>Type:</strong> {self.get_action_type_display()}</p>
                        <p><strong>Statut:</strong> {self.get_state_display()}</p>
                        <p><strong>Responsable:</strong> {self.owner_id.name}</p>
                        <p><strong>Date limite:</strong> {self.deadline}</p>
                        <p><strong>Progression:</strong> {self.progress}%</p>
                    </div>
                """,
                partner_ids=[(4, self.owner_id.user_id.partner_id.id)],
                message_type='notification',
                subtype_xmlid='mail.mt_comment'
            )

    def get_action_type_display(self):
        types = {
            'corrective': '🔧 Corrective',
            'preventive': '🛡️ Préventive',
            'improvement': '📈 Amélioration',
        }
        return types.get(self.action_type, self.action_type)

    def get_state_display(self):
        states = {
            'draft': '📝 Brouillon',
            'in_progress': '🔄 En cours',
            'review': '🔍 En relecture',
            'done': '✅ Terminé',
            'overdue': '⏰ En retard',
            'cancelled': '❌ Annulé',
        }
        return states.get(self.state, self.state)

    # ============================================================
    # MÉTHODES DE CLASSE
    # ============================================================

    @api.model
    def _cron_check_overdue_actions(self):
        """Cron pour vérifier les actions en retard"""
        today = fields.Date.today()
        overdue_actions = self.search([
            ('deadline', '<', today),
            ('state', 'not in', ['done', 'cancelled'])
        ])
        for action in overdue_actions:
            action.state = 'overdue'
        return True

    # ============================================================
    # SÉQUENCE
    # ============================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.corrective.action') or 'New'
        return super().create(vals_list)

    @api.model
    def _cron_send_reminders(self):
        """
        Cron pour envoyer des rappels automatiques :
        - Actions en retard
        - Actions proches de l'échéance (7 jours)
        """
        _logger.info("Démarrage du cron _cron_send_reminders")

        today = fields.Date.today()
        from datetime import timedelta

        # 1. Actions en retard
        overdue_actions = self.search([
            ('deadline', '<', today),
            ('state', 'not in', ['done', 'cancelled']),
        ])

        for action in overdue_actions:
            if action.owner_id and action.owner_id.user_id:
                self._send_reminder(action, 'overdue')
                _logger.info(f"Rappel envoyé pour l'action en retard {action.code} - {action.name}")

        # 2. Actions proches de l'échéance (7 jours)
        soon_actions = self.search([
            ('deadline', '=', today + timedelta(days=7)),
            ('state', 'not in', ['done', 'cancelled']),
            ('progress', '<', 80),
        ])

        for action in soon_actions:
            if action.owner_id and action.owner_id.user_id:
                self._send_reminder(action, 'soon')
                _logger.info(f"Rappel envoyé pour l'action proche échéance {action.code} - {action.name}")

        _logger.info("Fin du cron _cron_send_reminders")
        return True

    @api.model
    def _send_reminder(self, action, reminder_type):
        """
        Envoie un rappel pour une action
        """
        if not action.owner_id or not action.owner_id.user_id:
            return

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_url = f"{base_url}/web#id={action.id}&model=risk.corrective.action&view_type=form"

        if reminder_type == 'overdue':
            subject = f"⏰ RAPPEL : Action en retard - {action.name}"
            body = f"""
                <div style="font-family: Arial, sans-serif; padding: 15px; border: 1px solid #dc3545; border-radius: 8px; background: #fff5f5;">
                    <h3 style="color: #dc3545;">⏰ ACTION EN RETARD</h3>
                    <hr/>
                    <p><strong>Action :</strong> {action.name}</p>
                    <p><strong>Code :</strong> {action.code}</p>
                    <p><strong>Type :</strong> {action.get_action_type_display()}</p>
                    <p><strong>Responsable :</strong> {action.owner_id.name}</p>
                    <p><strong>Date limite :</strong> {action.deadline}</p>
                    <p><strong>Progression :</strong> {action.progress}%</p>
                    <p style="color: #dc3545;">⚠️ Cette action est en retard ! Veuillez prendre des mesures immédiates.</p>
                    <br/>
                    <a href="{action_url}" style="background:#dc3545;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">
                        🔗 Voir l'action
                    </a>
                </div>
                """
        else:  # 'soon'
            subject = f"⏰ Échéance dans 7 jours - {action.name}"
            body = f"""
                <div style="font-family: Arial, sans-serif; padding: 15px; border: 1px solid #fd7e14; border-radius: 8px; background: #fff8f0;">
                    <h3 style="color: #fd7e14;">⏰ ÉCHÉANCE DANS 7 JOURS</h3>
                    <hr/>
                    <p><strong>Action :</strong> {action.name}</p>
                    <p><strong>Code :</strong> {action.code}</p>
                    <p><strong>Type :</strong> {action.get_action_type_display()}</p>
                    <p><strong>Responsable :</strong> {action.owner_id.name}</p>
                    <p><strong>Date limite :</strong> {action.deadline}</p>
                    <p><strong>Progression :</strong> {action.progress}%</p>
                    <p style="color: #fd7e14;">⚠️ Cette action arrive bientôt à échéance. Veuillez accélérer la progression.</p>
                    <br/>
                    <a href="{action_url}" style="background:#fd7e14;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">
                        🔗 Voir l'action
                    </a>
                </div>
                """

        # Envoyer la notification
        action.message_post(
            body=body,
            subject=subject,
            partner_ids=[(4, action.owner_id.user_id.partner_id.id)],
            message_type='notification',
            subtype_xmlid='mail.mt_comment'
        )

    # ============================================================
    # MÉTHODE D'ACTION POUR ENVOYER UN RAPPEL MANUEL
    # ============================================================

    def action_send_reminder(self):
        """Envoie un rappel pour l'action (manuel)"""
        self.ensure_one()
        if self.owner_id and self.owner_id.user_id:
            self._send_reminder(self, 'overdue')
            self.reminder_sent = True
            self.last_reminder_date = fields.Date.today()
            return {
                'type': 'ir.actions.act_window',
                'name': 'Rappel envoyé',
                'res_model': 'risk.corrective.action',
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'current',
            }