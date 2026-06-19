from odoo import models, fields, api


class RiskAudit(models.Model):
    _name = 'risk.audit'
    _description = 'Audit Mission'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        readonly=True,
        default='New'
    )

    title = fields.Char(
        required=True
    )

    plan_id = fields.Many2one(
        'risk.audit.plan'
    )

    audit_type = fields.Selection(
        [
            ('internal', 'Internal Audit'),
            ('external', 'External Audit'),
            ('regulator', 'Regulator Audit'),
            ('it', 'IT Audit')
        ],
        required=True
    )

    process_ids = fields.Many2many(
        'risk.process'
    )

    organization_ids = fields.Many2many(
        'risk.organization'
    )

    start_date = fields.Date()

    end_date = fields.Date()

    lead_auditor_id = fields.Many2one(
        'hr.employee'
    )

    objective = fields.Html()

    scope = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('planning', 'Planning'),
            ('fieldwork', 'Fieldwork'),
            ('reporting', 'Reporting'),
            ('closed', 'Closed')
        ],
        default='draft'
    )

    finding_ids = fields.One2many(
        'risk.audit.finding',
        'audit_id'
    )

    finding_count = fields.Integer(
        compute='_compute_finding_count'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment'
    )

    @api.depends('finding_ids')
    def _compute_finding_count(self):
        for rec in self:
            rec.finding_count = len(
                rec.finding_ids
            )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('name', 'New') == 'New':

                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'risk.audit'
                )

        return super().create(vals_list)

    def action_view_findings(self):
        """Ouvre la vue des constats liés à cet audit"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Constats',
            'res_model': 'risk.finding',  # ou le nom du modèle des constats
            'view_mode': 'tree,form',
            'domain': [('audit_id', '=', self.id)],
            'context': {'default_audit_id': self.id},
        }
