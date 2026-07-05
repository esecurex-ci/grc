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