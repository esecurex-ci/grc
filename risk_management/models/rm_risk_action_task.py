from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskActionTask(models.Model):
    _name = 'risk.action.task'
    _description = 'Tâche du plan d\'action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'plan_id, sequence, deadline'
    _rec_name = 'name'

    # ============================================================
    # INFORMATIONS GÉNÉRALES
    # ============================================================

    name = fields.Char(
        string='Tâche',
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
    # ORDRE
    # ============================================================

    # ✅ AJOUT : Séquence pour l'ordre des tâches
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre d'affichage des tâches"
    )

    # ============================================================
    # LIEN VERS LE PLAN
    # ============================================================

    plan_id = fields.Many2one(
        'risk.action.plan',
        string='Plan d\'action',
        required=True,
        ondelete='cascade',
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

    # ============================================================
    # PLANIFICATION
    # ============================================================

    start_date = fields.Date(
        string='Date de début',
        default=fields.Date.today,
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
    # AVANCEMENT
    # ============================================================

    progress = fields.Float(
        string='Progression (%)',
        default=0,
        digits=(16, 2),
        tracking=True
    )

    state = fields.Selection([
        ('draft', '📝 À faire'),
        ('in_progress', '🔄 En cours'),
        ('review', '🔍 En relecture'),
        ('done', '✅ Terminé'),
        ('cancelled', '❌ Annulé'),
    ], string='Statut', default='draft', tracking=True, index=True)

    # ============================================================
    # PRIORITÉ
    # ============================================================

    priority = fields.Selection([
        ('low', '🟢 Basse'),
        ('medium', '🟡 Moyenne'),
        ('high', '🟠 Élevée'),
        ('critical', '🔴 Critique'),
    ], string='Priorité', default='medium', tracking=True, store=True)

    # ============================================================
    # RÉSULTATS
    # ============================================================

    result = fields.Html(
        string='Résultat'
    )

    # ============================================================
    # STATUT EN RETARD
    # ============================================================

    is_overdue = fields.Boolean(
        compute='_compute_is_overdue',
        string='En retard',
        store=True
    )

    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for record in self:
            if record.deadline and record.deadline < today and record.state not in ['done', 'cancelled']:
                record.is_overdue = True
            else:
                record.is_overdue = False

    # ============================================================
    # CONTRAINTES
    # ============================================================

    @api.constrains('progress')
    def _check_progress(self):
        for record in self:
            if record.progress < 0 or record.progress > 100:
                raise ValidationError(_("La progression doit être comprise entre 0 et 100%."))

    # ============================================================
    # MÉTHODES D'ACTION
    # ============================================================

    def action_start(self):
        """Démarrer la tâche"""
        self.ensure_one()
        self.state = 'in_progress'
        self.start_date = fields.Date.today()
        return True

    def action_review(self):
        """Soumettre à la relecture"""
        self.ensure_one()
        self.state = 'review'
        return True

    def action_done(self):
        """Terminer la tâche"""
        self.ensure_one()
        self.state = 'done'
        self.progress = 100
        self.end_date = fields.Date.today()
        return True

    def action_cancel(self):
        """Annuler la tâche"""
        self.ensure_one()
        self.state = 'cancelled'
        return True

    def action_reset_to_draft(self):
        """Remettre à faire"""
        self.ensure_one()
        self.state = 'draft'
        self.progress = 0
        return True

    # ============================================================
    # SÉQUENCE
    # ============================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('code'):
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.action.task') or 'New'
        return super().create(vals_list)