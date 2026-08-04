from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskActionPlan(models.Model):
    _name = 'risk.action.plan'
    _description = 'Plan d\'action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'deadline, name'
    _rec_name = 'name'

    # ============================================================
    # INFORMATIONS GÉNÉRALES
    # ============================================================

    name = fields.Char(
        string='Plan d\'action',
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

    # ============================================================
    # CONTEXTE
    # ============================================================

    risk_id = fields.Many2one(
        'risk.risk',
        string='Risque associé',
        tracking=True
    )

    assessment_id = fields.Many2one(
        'risk.assessment',
        string="Évaluation d'origine",
        tracking=True,
        help="Évaluation périodique à l'origine de ce plan d'action, si applicable "
             "(un plan d'action peut aussi être créé directement depuis un risque, "
             "un incident ou un contrôle, sans passer par une évaluation)."
    )

    incident_id = fields.Many2one(
        'risk.incident',
        string='Incident associé',
        tracking=True
    )

    control_id = fields.Many2one(
        'risk.control',
        string='Contrôle associé',
        tracking=True
    )

    control_test_id = fields.Many2one(
        'risk.control.test',
        string='Test de contrôle associé',
        tracking=True,
        help="Test de contrôle ayant révélé le besoin de ce plan d'action, le cas échéant "
             "(ex : un test en échec déclenche la création d'un plan correctif)."
    )

    action_type = fields.Selection([
        ('corrective', '🔧 Corrective'),
        ('preventive', '🛡️ Préventive'),
        ('improvement', '📈 Amélioration'),
    ], string="Type d'action", default='corrective', tracking=True)

    # ============================================================
    # RESPONSABLES
    # ============================================================

    owner_id = fields.Many2one(
        'hr.employee',
        string='Responsable du plan',
        required=True,
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

    start_date = fields.Date(
        string='Date de début',
        default=fields.Date.today,
        required=True,
        tracking=True
    )

    deadline = fields.Date(
        string='Date limite',
        required=True,
        tracking=True
    )

    end_date = fields.Date(
        string='Date de fin',
        tracking=True
    )

    # ============================================================
    # BUDGET
    # ============================================================

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

    # ============================================================
    # TÂCHES DU PLAN
    # ============================================================

    task_ids = fields.One2many(
        'risk.action.task',
        'plan_id',
        string='Tâches',
        copy=True
    )

    task_count = fields.Integer(
        compute='_compute_task_stats',
        string='Nombre de tâches'
    )

    task_completed_count = fields.Integer(
        compute='_compute_task_stats',
        string='Tâches terminées'
    )

    task_in_progress_count = fields.Integer(
        compute='_compute_task_stats',
        string='Tâches en cours'
    )

    task_progress = fields.Float(
        compute='_compute_task_stats',
        string='Progression du plan (%)'
    )

    # ============================================================
    # STATUT
    # ============================================================

    state = fields.Selection([
        ('draft', '📝 Brouillon'),
        ('approved', '✅ Approuvé'),
        ('in_progress', '🔄 En cours'),
        ('completed', '✅ Terminé'),
        ('cancelled', '❌ Annulé'),
    ], string='Statut', default='draft', tracking=True, index=True)

    # ============================================================
    # RAPPELS AUTOMATIQUES
    # (capacité reprise de l'ancien modèle risk.corrective.action,
    # désormais obsolète — voir cron dédié ci-dessous)
    # ============================================================

    reminder_sent = fields.Boolean(
        string='Rappel envoyé',
        default=False
    )

    last_reminder_date = fields.Date(
        string='Date du dernier rappel'
    )

    # ============================================================
    # COMPUTES
    # ============================================================

    @api.depends('task_ids', 'task_ids.state')
    def _compute_task_stats(self):
        for record in self:
            tasks = record.task_ids
            record.task_count = len(tasks)
            record.task_completed_count = len(tasks.filtered(lambda t: t.state == 'done'))
            record.task_in_progress_count = len(tasks.filtered(lambda t: t.state == 'in_progress'))

            if record.task_count > 0:
                record.task_progress = (record.task_completed_count / record.task_count) * 100
            else:
                record.task_progress = 0

    # ============================================================
    # CONTRAINTES
    # ============================================================

    @api.constrains('start_date', 'deadline')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.deadline and record.start_date > record.deadline:
                raise ValidationError(_("La date de début ne peut pas être postérieure à la date limite."))

    # ============================================================
    # MÉTHODES D'ACTION
    # ============================================================

    def action_approve(self):
        """Approuver le plan"""
        self.ensure_one()
        self.state = 'approved'
        return True

    def action_start(self):
        """Démarrer le plan"""
        self.ensure_one()
        self.state = 'in_progress'
        return True

    def action_complete(self):
        """Terminer le plan"""
        self.ensure_one()
        self.state = 'completed'
        self.end_date = fields.Date.today()
        return True

    def action_cancel(self):
        """Annuler le plan"""
        self.ensure_one()
        self.state = 'cancelled'
        return True

    def action_add_task(self):
        """Ajouter une tâche au plan"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ajouter une tâche - {self.name}',
            'res_model': 'risk.action.task',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_plan_id': self.id,
                'default_deadline': self.deadline,
            },
        }

    def action_view_tasks(self):
        """Voir toutes les tâches du plan"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Tâches - {self.name}',
            'res_model': 'risk.action.task',
            'view_mode': 'list,form,kanban',
            'domain': [('plan_id', '=', self.id)],
        }

    # ============================================================
    # SÉQUENCE
    # ============================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.action.plan') or 'New'
        return super().create(vals_list)

    # ============================================================
    # RAPPELS AUTOMATIQUES (repris de l'ancien risk.corrective.action)
    # ============================================================

    @api.model
    def _cron_send_reminders(self):
        """
        Cron quotidien envoyant des rappels automatiques :
        - Plans en retard (échéance dépassée, non terminés/annulés)
        - Plans à échéance dans 7 jours, peu avancés (< 80%)
        """
        today = fields.Date.today()
        from datetime import timedelta

        overdue_plans = self.search([
            ('deadline', '<', today),
            ('state', 'not in', ['completed', 'cancelled']),
        ])
        for plan in overdue_plans:
            if plan.owner_id and plan.owner_id.user_id:
                plan._send_reminder('overdue')

        soon_plans = self.search([
            ('deadline', '=', today + timedelta(days=7)),
            ('state', 'not in', ['completed', 'cancelled']),
            ('task_progress', '<', 80),
        ])
        for plan in soon_plans:
            if plan.owner_id and plan.owner_id.user_id:
                plan._send_reminder('soon')

        return True

    def _send_reminder(self, reminder_type):
        """Envoie un rappel (chatter) pour ce plan d'action au responsable."""
        self.ensure_one()
        if not self.owner_id or not self.owner_id.user_id:
            return

        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        action_url = f"{base_url}/web#id={self.id}&model=risk.action.plan&view_type=form"

        if reminder_type == 'overdue':
            subject = f"⏰ RAPPEL : Plan d'action en retard - {self.name}"
            color = '#dc3545'
            title = '⏰ PLAN D\'ACTION EN RETARD'
            message = "⚠️ Ce plan d'action est en retard ! Veuillez prendre des mesures immédiates."
        else:  # 'soon'
            subject = f"⏰ Échéance dans 7 jours - {self.name}"
            color = '#fd7e14'
            title = '⏰ ÉCHÉANCE DANS 7 JOURS'
            message = "⚠️ Ce plan d'action arrive bientôt à échéance. Veuillez accélérer la progression."

        body = f"""
            <div style="font-family: Arial, sans-serif; padding: 15px; border: 1px solid {color}; border-radius: 8px;">
                <h3 style="color: {color};">{title}</h3>
                <hr/>
                <p><strong>Plan :</strong> {self.name}</p>
                <p><strong>Code :</strong> {self.code}</p>
                <p><strong>Responsable :</strong> {self.owner_id.name}</p>
                <p><strong>Date limite :</strong> {self.deadline}</p>
                <p><strong>Progression :</strong> {self.task_progress:.0f}%</p>
                <p style="color: {color};">{message}</p>
                <br/>
                <a href="{action_url}" style="background:{color};color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">
                    🔗 Voir le plan d'action
                </a>
            </div>
        """

        self.message_post(
            body=body,
            subject=subject,
            partner_ids=[(4, self.owner_id.user_id.partner_id.id)],
            message_type='notification',
            subtype_xmlid='mail.mt_comment',
        )
        self.reminder_sent = True
        self.last_reminder_date = fields.Date.today()

    def action_send_reminder(self):
        """Envoie un rappel manuel pour ce plan d'action."""
        self.ensure_one()
        self._send_reminder('overdue')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Rappel envoyé',
            'res_model': 'risk.action.plan',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }