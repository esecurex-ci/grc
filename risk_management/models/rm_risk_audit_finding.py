from odoo import models, fields


class RiskAuditFinding(models.Model):
    _name = 'risk.audit.finding'
    _description = 'Audit Finding'
    _inherit = ['mail.thread']

    name = fields.Char(
        readonly=True,
        default='New'
    )

    audit_id = fields.Many2one(
        'risk.audit',
        required=True,
        ondelete='cascade'
    )

    title = fields.Char(
        required=True
    )

    description = fields.Html()

    risk_id = fields.Many2one(
        'risk.risk'
    )

    control_id = fields.Many2one(
        'risk.control'
    )

    severity = fields.Selection(
        [
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('critical', 'Critical')
        ],
        default='moderate'
    )

    root_cause = fields.Html()

    recommendation_ids = fields.One2many(
        'risk.audit.recommendation',
        'finding_id'
    )

    state = fields.Selection(
        [
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('closed', 'Closed')
        ],
        default='open'
    )
    regulation_ids = fields.Many2many(
        'risk.regulation'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment'
    )
    compliance_requirement_ids = fields.Many2many(
        'risk.compliance.requirement',
        string='Compliance Requirements'
    )