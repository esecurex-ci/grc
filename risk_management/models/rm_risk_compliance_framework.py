from odoo import models, fields, api


class RiskComplianceFramework(models.Model):
    _name = 'risk.compliance.framework'
    _description = 'Compliance Framework'
    _inherit = ['mail.thread']

    name = fields.Char(
        required=True
    )

    code = fields.Char()

    version = fields.Char()

    publisher = fields.Char()

    publication_date = fields.Date()

    description = fields.Html()

    active = fields.Boolean(
        default=True
    )

    requirement_ids = fields.One2many(
        'risk.compliance.requirement',
        'framework_id'
    )
    requirement_count = fields.Integer(
        compute='_compute_statistics'
    )

    @api.depends('requirement_ids')
    def _compute_statistics(self):
        for rec in self:
            rec.requirement_count = len(
                rec.requirement_ids
            )

    def action_view_requirements(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Requirements',
            'res_model': 'risk.compliance.requirement',
            'view_mode': 'list,form',
            'domain': [
                ('framework_id', '=', self.id)
            ],
            'context': {
                'default_framework_id': self.id
            }
        }