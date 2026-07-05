from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class RiskCorrectiveAction(models.Model):
    _name = 'risk.corrective.action'
    _description = 'Action corrective / Plan d\'action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'deadline, state'

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

    incident_id = fields.Many2one(
        'risk.incident',
        string='Incident associé',
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

    # ✅ CORRIGÉ : due_date → deadline (avec alias)
    deadline = fields.Date(
        string='Date limite',
        required=True,
        tracking=True,
        help="Date limite de réalisation de l'action"
    )

    # ✅ Alias pour compatibilité
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
        default=1,
        help="Durée estimée en heures"
    )

    actual_duration = fields.Float(
        string='Durée réelle (heures)',
        help="Durée réelle en heures"
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
        ('review', '🔍 En revue'),
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

    # ============================================================
    # COMPUTES
    # ============================================================

    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            if record.deadline and record.deadline < today and record.state not in ['done', 'cancelled']:
                record.is_overdue = True
                # Mettre à jour le statut si nécessaire
                if record.state not in ['overdue']:
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
        return True

    def action_review(self):
        """Soumettre à la revue"""
        self.ensure_one()
        self.state = 'review'
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
            if not vals.get('code') or vals['code'] == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.corrective.action') or 'New'
        return super().create(vals_list)

    # ============================================================
    # CHAMPS POUR LES NOTIFICATIONS
    # ============================================================

    notification_sent = fields.Boolean(
        string='Notification envoyée',
        default=False,
        help="Indique si la notification de démarrage a été envoyée"
    )

    reminder_sent = fields.Boolean(
        string='Rappel envoyé',
        default=False,
        help="Indique si un rappel a été envoyé"
    )

    last_reminder_date = fields.Date(
        string='Date du dernier rappel'
    )

    # ============================================================
    # MÉTHODES DE NOTIFICATION
    # ============================================================

    def action_start(self):
        """Démarrer l'action et envoyer les notifications"""
        self.ensure_one()
        self.state = 'in_progress'
        self.start_date = fields.Date.today()

        # ✅ Envoyer les notifications
        self._send_start_notifications()

        # ✅ Créer une activité (to-do) pour le responsable
        self._create_activity()

        return True

    def _send_start_notifications(self):
        """Envoie les notifications de démarrage"""
        self.ensure_one()

        # 1. Notifier le responsable
        if self.owner_id and self.owner_id.user_id:
            self._send_notification(
                partner_id=self.owner_id.user_id.partner_id.id,
                subject=f"📋 Action démarrée : {self.name}",
                body=self._get_notification_body('start')
            )

        # 2. Notifier le relecteur (si présent)
        if self.reviewer_id and self.reviewer_id.user_id:
            self._send_notification(
                partner_id=self.reviewer_id.user_id.partner_id.id,
                subject=f"📋 Action en cours : {self.name}",
                body=self._get_notification_body('review')
            )

        # 3. Notifier l'approbateur (si présent)
        if self.approver_id and self.approver_id.user_id:
            self._send_notification(
                partner_id=self.approver_id.user_id.partner_id.id,
                subject=f"📋 Action en cours : {self.name}",
                body=self._get_notification_body('approve')
            )

        # 4. Notifier les abonnés (followers)
        self._notify_followers()

        self.notification_sent = True

        _logger.info(f"Notifications envoyées pour l'action {self.code} - {self.name}")

    def _send_notification(self, partner_id, subject, body):
        """Envoie une notification par email et message interne"""
        self.ensure_one()

        # Message interne (dans le chatter)
        self.message_post(
            body=body,
            subject=subject,
            partner_ids=[(4, partner_id)],
            message_type='notification',
            subtype_xmlid='mail.mt_comment'
        )

        # Email (optionnel)
        try:
            template = self.env.ref('risk_management.email_template_action_notification', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
        except Exception as e:
            _logger.warning(f"Erreur d'envoi d'email pour l'action {self.code}: {e}")

    def _get_notification_body(self, notification_type):
        """Génère le corps du message de notification"""
        self.ensure_one()

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_url = f"{base_url}/web#id={self.id}&model=risk.corrective.action&view_type=form"

        bodies = {
            'start': f"""
                <div style="font-family: Arial, sans-serif; padding: 15px;">
                    <h3>📋 Action corrective démarrée</h3>
                    <p><strong>Action :</strong> {self.name}</p>
                    <p><strong>Code :</strong> {self.code}</p>
                    <p><strong>Type :</strong> {self.get_action_type_display()}</p>
                    <p><strong>Date de début :</strong> {self.start_date}</p>
                    <p><strong>Date limite :</strong> {self.deadline}</p>
                    <p><strong>Responsable :</strong> {self.owner_id.name if self.owner_id else 'Non défini'}</p>
                    <p><strong>Risque associé :</strong> {self.risk_id.name if self.risk_id else 'Aucun'}</p>
                    <p><strong>Progression :</strong> {self.progress}%</p>
                    <br/>
                    <a href="{action_url}" style="background:#1a237e;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">
                        🔗 Voir l'action
                    </a>
                </div>
            """,
            'review': f"""
                <div style="font-family: Arial, sans-serif; padding: 15px;">
                    <h3>🔍 Action en attente de relecture</h3>
                    <p><strong>Action :</strong> {self.name}</p>
                    <p><strong>Code :</strong> {self.code}</p>
                    <p><strong>Responsable :</strong> {self.owner_id.name if self.owner_id else 'Non défini'}</p>
                    <p><strong>Progression :</strong> {self.progress}%</p>
                    <p>Veuillez relire l'action et valider la progression.</p>
                    <br/>
                    <a href="{action_url}" style="background:#1a237e;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">
                        🔗 Voir l'action
                    </a>
                </div>
            """,
            'approve': f"""
                <div style="font-family: Arial, sans-serif; padding: 15px;">
                    <h3>✅ Action en attente d'approbation</h3>
                    <p><strong>Action :</strong> {self.name}</p>
                    <p><strong>Code :</strong> {self.code}</p>
                    <p><strong>Responsable :</strong> {self.owner_id.name if self.owner_id else 'Non défini'}</p>
                    <p><strong>Progression :</strong> {self.progress}%</p>
                    <p>Veuillez approuver l'action.</p>
                    <br/>
                    <a href="{action_url}" style="background:#1a237e;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">
                        🔗 Voir l'action
                    </a>
                </div>
            """,
            'reminder': f"""
                <div style="font-family: Arial, sans-serif; padding: 15px;">
                    <h3>⏰ Rappel : Action en retard</h3>
                    <p><strong>Action :</strong> {self.name}</p>
                    <p><strong>Code :</strong> {self.code}</p>
                    <p><strong>Date limite :</strong> {self.deadline}</p>
                    <p><strong>Retard :</strong> {self.days_remaining} jours</p>
                    <p>Veuillez prendre les mesures nécessaires.</p>
                    <br/>
                    <a href="{action_url}" style="background:#dc3545;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">
                        🔗 Voir l'action
                    </a>
                </div>
            """
        }

        return bodies.get(notification_type, bodies['start'])

    def get_action_type_display(self):
        """Retourne le libellé du type d'action"""
        types = {
            'corrective': '🔧 Corrective',
            'preventive': '🛡️ Préventive',
            'improvement': '📈 Amélioration',
        }
        return types.get(self.action_type, self.action_type)

    def _create_activity(self):
        """Crée une activité (to-do) pour le responsable"""
        self.ensure_one()

        if self.owner_id and self.owner_id.user_id:
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f"Action corrective : {self.name}",
                'note': f"""
                    <p><strong>Action :</strong> {self.name}</p>
                    <p><strong>Code :</strong> {self.code}</p>
                    <p><strong>Date limite :</strong> {self.deadline}</p>
                    <p><strong>Description :</strong> {self.description}</p>
                """,
                'user_id': self.owner_id.user_id.id,
                'res_model_id': self.env['ir.model']._get('risk.corrective.action').id,
                'res_id': self.id,
                'date_deadline': self.deadline,
            })

    def _notify_followers(self):
        """Notifie les abonnés du risque associé"""
        self.ensure_one()

        if self.risk_id:
            followers = self.risk_id.message_follower_ids.mapped('partner_id')
            if followers:
                self.message_post(
                    body=f"""
                        <div style="font-family: Arial, sans-serif; padding: 10px;">
                            <h4>📋 Nouvelle action corrective</h4>
                            <p><strong>Action :</strong> {self.name}</p>
                            <p><strong>Code :</strong> {self.code}</p>
                            <p><strong>Risque :</strong> {self.risk_id.name}</p>
                            <p><strong>Responsable :</strong> {self.owner_id.name if self.owner_id else 'Non défini'}</p>
                            <p><strong>Date limite :</strong> {self.deadline}</p>
                        </div>
                    """,
                    partner_ids=[(4, p.id) for p in followers],
                    message_type='notification',
                    subtype_xmlid='mail.mt_comment'
                )

    def action_send_reminder(self):
        """Envoie un rappel pour les actions en retard"""
        self.ensure_one()

        if self.owner_id and self.owner_id.user_id:
            self._send_notification(
                partner_id=self.owner_id.user_id.partner_id.id,
                subject=f"⏰ Rappel : Action en retard - {self.name}",
                body=self._get_notification_body('reminder')
            )

            # Créer une activité de rappel
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'summary': f"⏰ RAPPEL : Action en retard - {self.name}",
                'note': f"""
                    <p><strong>Action :</strong> {self.name}</p>
                    <p><strong>Code :</strong> {self.code}</p>
                    <p><strong>Date limite dépassée depuis :</strong> {self.days_remaining} jours</p>
                    <p><strong>Progression :</strong> {self.progress}%</p>
                    <p style="color:#dc3545;">⚠️ Action en retard ! Veuillez prendre des mesures immédiates.</p>
                """,
                'user_id': self.owner_id.user_id.id,
                'res_model_id': self.env['ir.model']._get('risk.corrective.action').id,
                'res_id': self.id,
                'date_deadline': fields.Date.today(),
            })

            self.reminder_sent = True
            self.last_reminder_date = fields.Date.today()

    # ============================================================
    # CRON POUR LES RAPPELS
    # ============================================================

    @api.model
    def _cron_send_reminders(self):
        """Cron pour envoyer des rappels automatiques"""
        # Actions en retard
        overdue_actions = self.search([
            ('deadline', '<', fields.Date.today()),
            ('state', 'not in', ['done', 'cancelled']),
            ('reminder_sent', '=', False)
        ])

        for action in overdue_actions:
            action.action_send_reminder()
            _logger.info(f"Rappel envoyé pour l'action {action.code} - {action.name}")

        # Actions proches de l'échéance (7 jours)
        from datetime import timedelta
        soon_actions = self.search([
            ('deadline', '=', fields.Date.today() + timedelta(days=7)),
            ('state', 'not in', ['done', 'cancelled']),
            ('progress', '<', 80)
        ])

        for action in soon_actions:
            if action.owner_id and action.owner_id.user_id:
                action._send_notification(
                    partner_id=action.owner_id.user_id.partner_id.id,
                    subject=f"⏰ Échéance dans 7 jours : {action.name}",
                    body=f"""
                        <div style="font-family: Arial, sans-serif; padding: 15px;">
                            <h3>⏰ Échéance dans 7 jours</h3>
                            <p><strong>Action :</strong> {action.name}</p>
                            <p><strong>Code :</strong> {action.code}</p>
                            <p><strong>Date limite :</strong> {action.deadline}</p>
                            <p><strong>Progression :</strong> {action.progress}%</p>
                            <p>Veuillez accélérer la progression de l'action.</p>
                            <br/>
                            <a href="{self.env['ir.config_parameter'].sudo().get_param('web.base.url')}/web#id={action.id}&model=risk.corrective.action&view_type=form" 
                               style="background:#fd7e14;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">
                                🔗 Voir l'action
                            </a>
                        </div>
                    """
                )