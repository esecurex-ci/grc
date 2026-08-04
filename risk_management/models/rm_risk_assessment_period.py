from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RiskAssessmentPeriod(models.Model):
    _name = 'risk.assessment.period'
    _description = 'Evaluation périodique des risques'
    _order = 'date_start desc'

    name = fields.Char(
        required=True,
        string='Désignation',
    )

    code = fields.Char(string='Code')

    date_start = fields.Date(
        required=True,
        string='Date de début'
    )

    date_end = fields.Date(
        required=True,
        string='Date clôture'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('open', 'Ouvert'),
            ('closed', 'Clôturé')
        ],
        default='draft',
        tracking=True,
        string='Status'
    )

    active = fields.Boolean(
        default=True
    )

    assessment_ids = fields.One2many(
        'risk.assessment',
        'period_id',
        string='Evaluations',
    )

    assessment_count = fields.Integer(
        compute='_compute_assessment_count',
        string='Evaluations',
    )

    my_risk_ids = fields.Many2many(
        'risk.risk',
        compute='_compute_my_risk_ids',
        string='Mes risques à évaluer',
        help="Risques dont l'utilisateur connecté est propriétaire (owner_id), "
             "pour lancer directement son auto-évaluation en un clic plutôt que "
             "de rechercher un risque dans une liste générale."
    )

    @api.depends('assessment_ids')
    def _compute_assessment_count(self):
        for rec in self:
            rec.assessment_count = len(rec.assessment_ids)

    @api.depends()
    def _compute_my_risk_ids(self):
        employee = self.env.user.employee_id
        risks = self.env['risk.risk'].search([
            ('owner_id', '=', employee.id),
            ('active', '=', True),
        ]) if employee else self.env['risk.risk']
        for rec in self:
            rec.my_risk_ids = risks

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end < rec.date_start:
                raise ValidationError(
                    "La date de clôture doit être supérieure à la date de début."
                )