from odoo import models, fields, api


class RiskAuditScope(models.Model):
    _name = 'risk.audit.scope'
    _description = 'Audit Scope'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]
    _order = 'name'

    name = fields.Char(
        string='Scope Name',
        required=True,
        tracking=True
    )

    audit_id = fields.Many2one(
        'risk.audit',
        string='Audit Mission',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    scope_type = fields.Selection(
        [
            ('process', 'Process'),
            ('organization', 'Organization'),
            ('risk', 'Risk'),
            ('control', 'Control'),
            ('asset', 'Asset'),
            ('regulation', 'Regulation'),
            ('other', 'Other')
        ],
        string='Scope Type',
        required=True,
        default='process',
        tracking=True
    )

    process_id = fields.Many2one(
        'risk.process',
        string='Process'
    )

    organization_id = fields.Many2one(
        'risk.organization',
        string='Organization Unit'
    )

    risk_id = fields.Many2one(
        'risk.risk',
        string='Risk'
    )

    control_id = fields.Many2one(
        'risk.control',
        string='Control'
    )

    asset_id = fields.Many2one(
        'risk.asset',
        string='Asset'
    )

    regulation_id = fields.Many2one(
        'risk.regulation',
        string='Regulation'
    )

    description = fields.Html(
        string='Description'
    )

    owner_id = fields.Many2one(
        'hr.employee',
        string='Owner'
    )

    active = fields.Boolean(
        default=True
    )

    display_name_scope = fields.Char(
        compute='_compute_display_name_scope',
        store=True
    )

    @api.depends(
        'scope_type',
        'process_id',
        'organization_id',
        'risk_id',
        'control_id',
        'asset_id',
        'regulation_id'
    )
    def _compute_display_name_scope(self):

        for rec in self:

            value = ''

            if rec.scope_type == 'process':
                value = rec.process_id.name or ''

            elif rec.scope_type == 'organization':
                value = rec.organization_id.name or ''

            elif rec.scope_type == 'risk':
                value = rec.risk_id.name or ''

            elif rec.scope_type == 'control':
                value = rec.control_id.name or ''

            elif rec.scope_type == 'asset':
                value = rec.asset_id.name or ''

            elif rec.scope_type == 'regulation':
                value = rec.regulation_id.name or ''

            rec.display_name_scope = value