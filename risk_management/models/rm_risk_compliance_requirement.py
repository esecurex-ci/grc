from odoo import models, fields, api


class RiskComplianceRequirement(models.Model):
    _name = 'risk.compliance.requirement'
    _description = 'Compliance Requirement'
    _inherit = ['mail.thread']

    code = fields.Char(
        required=True
    )

    title = fields.Char(
        required=True
    )

    framework_id = fields.Many2one(
        'risk.compliance.framework',
        required=True,
        ondelete='cascade'
    )

    article = fields.Char()

    description = fields.Html()

    mandatory = fields.Boolean(
        default=True
    )

    risk_ids = fields.Many2many(
        'risk.risk',
        string='Related Risks'
    )

    control_ids = fields.Many2many(
        'risk.control',
        string='Controls'
    )

    audit_finding_ids = fields.Many2many(
        'risk.audit.finding',
        string='Audit Findings'
    )

    active = fields.Boolean(
        default=True
    )
    mapping_ids = fields.One2many(
        'risk.compliance.mapping',
        'requirement_id'
    )

    control_test_ids = fields.One2many(
        'risk.compliance.control.test',
        'requirement_id'
    )
    assessment_count = fields.Integer(
        compute='_compute_statistics'
    )

    obligation_count = fields.Integer(
        compute='_compute_statistics'
    )

    test_count = fields.Integer(
        compute='_compute_statistics'
    )

    @api.depends(
        'control_test_ids'
    )
    def _compute_statistics(self):
        assessment_obj = self.env[
            'risk.compliance.assessment'
        ]

        obligation_obj = self.env[
            'risk.compliance.obligation'
        ]

        for rec in self:
            rec.assessment_count = assessment_obj.search_count([
                ('requirement_id', '=', rec.id)
            ])

            rec.obligation_count = obligation_obj.search_count([
                ('requirement_id', '=', rec.id)
            ])

            rec.test_count = len(
                rec.control_test_ids
            )

    def action_view_assessments(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Assessments',
            'res_model': 'risk.compliance.assessment',
            'view_mode': 'list,form',
            'domain': [
                ('requirement_id', '=', self.id)
            ]
        }

    def action_view_obligations(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Obligations',
            'res_model': 'risk.compliance.obligation',
            'view_mode': 'list,form',
            'domain': [
                ('requirement_id', '=', self.id)
            ]
        }

    def action_view_control_tests(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Control Tests',
            'res_model': 'risk.compliance.control.test',
            'view_mode': 'list,form',
            'domain': [
                ('requirement_id', '=', self.id)
            ]
        }
