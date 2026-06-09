from odoo import models, fields


class RiskAuditScope(models.Model):
    _name = 'risk.audit.scope'
    _description = 'Audit Scope'

    audit_id = fields.Many2one(
        'risk.audit',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        required=True
    )

    description = fields.Html()