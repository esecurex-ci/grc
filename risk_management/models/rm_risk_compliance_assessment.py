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
    evidence_count = fields.Integer(
        compute='_compute_statistics'
    )

    action_plan_count = fields.Integer(
        compute='_compute_statistics'
    )

    @api.depends(
        'evidence_ids',
        'action_plan_ids'
    )
    def _compute_statistics(self):

        for rec in self:
            rec.evidence_count = len(
                rec.evidence_ids
            )

            rec.action_plan_count = len(
                rec.action_plan_ids
            )

    def action_view_evidence(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Evidence',
            'res_model': 'risk.compliance.evidence',
            'view_mode': 'list,form',
            'domain': [
                ('assessment_id', '=', self.id)
            ]
        }

    def action_view_action_plans(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Action Plans',
            'res_model': 'risk.compliance.action.plan',
            'view_mode': 'list,form',
            'domain': [
                ('assessment_id', '=', self.id)
            ]
        }



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