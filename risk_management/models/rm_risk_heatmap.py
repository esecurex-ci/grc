from odoo import models, fields, api


class RiskHeatmap(models.Model):
    _name = 'risk.heatmap'
    _description = 'Risk Heatmap'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'assessment_date desc'

    name = fields.Char(
        required=True,
        tracking=True
    )

    assessment_date = fields.Date(
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    period_id = fields.Many2one(
        'risk.assessment.period',
        tracking=True
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company
    )

    line_ids = fields.One2many(
        'risk.heatmap.line',
        'heatmap_id'
    )

    total_risks = fields.Integer(
        compute='_compute_statistics'
    )

    critical_risks = fields.Integer(
        compute='_compute_statistics'
    )

    high_risks = fields.Integer(
        compute='_compute_statistics'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('validated', 'Validated')
        ],
        default='draft',
        tracking=True
    )

    @api.depends('line_ids')
    def _compute_statistics(self):

        for rec in self:

            rec.total_risks = len(rec.line_ids)

            rec.critical_risks = len(
                rec.line_ids.filtered(
                    lambda r: r.risk_level == 'critical'
                )
            )

            rec.high_risks = len(
                rec.line_ids.filtered(
                    lambda r: r.risk_level == 'high'
                )
            )

    def action_validate(self):
        self.write({
            'state': 'validated'
        })

    def action_generate(self):

        self.line_ids.unlink()

        assessments = self.env[
            'risk.assessment'
        ].search([
            ('state', '=', 'approved')
        ])

        for assessment in assessments:
            self.env[
                'risk.heatmap.line'
            ].create({

                'heatmap_id':
                    self.id,

                'risk_id':
                    assessment.risk_id.id,

                'assessment_id':
                    assessment.id,

                'probability':
                    assessment.residual_probability,

                'impact':
                    assessment.residual_impact,

                'score':
                    assessment.residual_score,

                'risk_level':
                    assessment.risk_level,

            })