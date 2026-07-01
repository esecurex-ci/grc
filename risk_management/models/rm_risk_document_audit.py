from odoo import api, fields, models, _


class RiskDocumentAudit(models.Model):
    _name = 'risk.document.audit'
    _description = 'Audit de document de gouvernance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc, document_id'

    document_id = fields.Many2one(
        'risk.document',
        string='Document',
        required=True,
        ondelete='cascade',
        index=True
    )

    auditor_id = fields.Many2one(
        'hr.employee',
        string='Auditeur',
        required=True,
        tracking=True
    )

    audit_date = fields.Date(
        string="Date d'audit",
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    status = fields.Selection([
        ('planned', '📅 Planifié'),
        ('in_progress', '🔄 En cours'),
        ('completed', '✅ Terminé'),
    ], string='Statut', default='planned', tracking=True)

    findings = fields.Html(
        string='Constatations',
        tracking=True
    )

    recommendations = fields.Html(
        string='Recommandations',
        tracking=True
    )

    compliance_score = fields.Float(
        string='Score de conformité',
        digits=(16, 2),
        tracking=True
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'risk_document_audit_attachment_rel',
        'audit_id',
        'attachment_id',
        string='Pièces jointes'
    )

    def action_start_audit(self):
        self.ensure_one()
        self.status = 'in_progress'
        return True

    def action_complete_audit(self):
        self.ensure_one()
        self.status = 'completed'
        return True