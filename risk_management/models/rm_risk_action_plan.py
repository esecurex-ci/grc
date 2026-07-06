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

    @api.depends('task_ids', 'task_ids.state')
    def _compute_completion_rate(self):
        for record in self:
            if record.task_count > 0:
                completed = len(record.task_ids.filtered(lambda t: t.state == 'done'))
                record.completion_rate = (completed / record.task_count) * 100
            else:
                record.completion_rate = 0

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