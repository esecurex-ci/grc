from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RiskAssessmentPeriod(models.Model):
    _name = 'risk.assessment.period'
    _description = 'Evaluation périodique des risques'
    _order = 'date_start desc'

    name = fields.Char(
        required=True,
        string='Nom',
    )

    code = fields.Char()

    date_start = fields.Date(
        required=True
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
        tracking=True
    )

    active = fields.Boolean(
        default=True
    )

    assessment_ids = fields.One2many(
        'risk.assessment',
        'period_id',
        string='Assessments',
    )

    assessment_count = fields.Integer(
        compute='_compute_assessment_count',
        string='Assessments',
    )

    @api.depends('assessment_ids')
    def _compute_assessment_count(self):
        for rec in self:
            rec.assessment_count = len(rec.assessment_ids)

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end < rec.date_start:
                raise ValidationError(
                    "La date de clôture doit être supérieure à la date de début."
                )