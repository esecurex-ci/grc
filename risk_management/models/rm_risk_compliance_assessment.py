from odoo import models, fields, api


class RiskComplianceAssessment(models.Model):
    _name = 'risk.compliance.assessment'
    _description = 'Compliance Assessment'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        readonly=True,
        default='New'
    )

    assessment_date = fields.Date(
        required=True
    )

    assessor_id = fields.Many2one(
        'hr.employee'
    )

    requirement_id = fields.Many2one(
        'risk.compliance.requirement',
        required=True
    )

    compliance_level = fields.Selection(
        [
            ('compliant', 'Compliant'),
            ('partially', 'Partially Compliant'),
            ('non_compliant', 'Non Compliant')
        ],
        required=True
    )

    score = fields.Float()

    comment = fields.Html()

    evidence_ids = fields.One2many(
        'risk.compliance.evidence',
        'assessment_id'
    )

    action_plan_ids = fields.One2many(
        'risk.compliance.action.plan',
        'assessment_id'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('validated', 'Validated')
        ],
        default='draft'
    )
    compliance_percentage = fields.Float(
        compute='_compute_compliance_percentage',
        store=True
    )

    from odoo import api

    @api.depends('compliance_level')
    def _compute_compliance_percentage(self):

        mapping = {
            'compliant': 100,
            'partially': 50,
            'non_compliant': 0
        }

        for rec in self:
            rec.compliance_percentage = mapping.get(rec.compliance_level,0 )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('name', 'New') == 'New':

                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'risk.compliance.assessment'
                )

        return super().create(vals_list)