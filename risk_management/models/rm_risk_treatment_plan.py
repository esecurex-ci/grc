from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RiskTreatmentPlan(models.Model):
    _name = 'risk.treatment.plan'
    _description = 'Risk Treatment Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'target_date, name'

    # =====================================================
    # CHAMPS PRINCIPAUX
    # =====================================================

    name = fields.Char(
        string='Plan Name',
        required=True,
        tracking=True
    )

    assessment_id = fields.Many2one(
        'risk.assessment',
        string='Assessment',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    risk_id = fields.Many2one(
        'risk.risk',
        string='Risk',
        related='assessment_id.risk_id',
        store=True,
        readonly=True
    )

    # ✅ Correction : utiliser risk.function au lieu de hr.employee
    owner_id = fields.Many2one(
        'risk.function',
        string='Action Owner (Function)',
        tracking=True
    )

    # ✅ Optionnel : garder un champ pour l'employé (information)
    owner_employee_id = fields.Many2one(
        'hr.employee',
        string='Action Owner (Employee)',
        tracking=True
    )

    description = fields.Html(
        string='Description',
        tracking=True
    )

    # =====================================================
    # DATES
    # =====================================================

    target_date = fields.Date(
        string='Target Date',
        required=True,
        tracking=True
    )

    completion_date = fields.Date(
        string='Completion Date',
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
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # =====================================================
    # PROGRESS & STATE
    # =====================================================

    progress = fields.Float(
        string='Progress',
        default=0,
        tracking=True,
        help='Progress percentage (0-100)'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        string='Status',
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
        string='Is Overdue'
    )

    days_remaining = fields.Integer(
        compute='_compute_is_overdue',
        store=True,
        string='Days Remaining'
    )

    # =====================================================
    # CONSTRAINTS
    # =====================================================

    @api.constrains('progress')
    def _check_progress(self):
        for record in self:
            if record.progress < 0 or record.progress > 100:
                raise ValidationError("Progress must be between 0 and 100.")

    @api.constrains('target_date', 'completion_date')
    def _check_dates(self):
        for record in self:
            if record.target_date and record.completion_date:
                if record.completion_date < record.target_date:
                    raise ValidationError("Completion date cannot be before target date.")

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

    def action_start(self):
        """Démarrer le plan de traitement"""
        for record in self:
            if record.state != 'draft':
                raise ValidationError("Only draft plans can be started.")
            record.write({
                'state': 'in_progress'
            })

    def action_complete(self):
        """Terminer le plan de traitement"""
        for record in self:
            if record.state != 'in_progress':
                raise ValidationError("Only in-progress plans can be completed.")
            record.write({
                'state': 'completed',
                'progress': 100,
                'completion_date': fields.Date.today()
            })

    def action_cancel(self):
        """Annuler le plan de traitement"""
        for record in self:
            if record.state in ['completed', 'cancelled']:
                raise ValidationError("Completed or cancelled plans cannot be cancelled.")
            record.write({
                'state': 'cancelled'
            })

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
                raise ValidationError("Cannot update progress of completed plans.")
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
            'name': 'Risk',
            'res_model': 'risk.risk',
            'view_mode': 'form',
            'res_id': self.risk_id.id,
        }

    def action_view_assessment(self):
        """Voir l'évaluation associée"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assessment',
            'res_model': 'risk.assessment',
            'view_mode': 'form',
            'res_id': self.assessment_id.id,
        }