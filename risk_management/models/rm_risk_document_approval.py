from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskDocumentApproval(models.Model):
    _name = 'risk.document.approval'
    _description = 'Approbation de document de gouvernance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc, document_id'
    _rec_name = 'document_id'

    # =====================================================
    # RELATIONS
    # =====================================================

    document_id = fields.Many2one(
        'risk.document',
        string='Document',
        required=True,
        ondelete='cascade',
        index=True
    )

    version_id = fields.Many2one(
        'risk.document.version',
        string='Version',
        ondelete='set null',
        help="Version du document approuvée"
    )

    # =====================================================
    # INFORMATIONS D'APPROBATION
    # =====================================================

    approver_id = fields.Many2one(
        'hr.employee',
        string='Approbateur',
        required=True,
        tracking=True
    )

    approval_date = fields.Date(
        string="Date d'approbation",
        default=fields.Date.today,
        tracking=True
    )

    status = fields.Selection([
        ('pending', '⏳ En attente'),
        ('approved', '✅ Approuvé'),
        ('rejected', '❌ Rejeté'),
        ('conditionnal', '⚠️ Approbation conditionnelle'),
    ], string='Statut', default='pending', tracking=True, index=True)

    # =====================================================
    # COMMENTAIRES
    # =====================================================

    comments = fields.Html(
        string='Commentaires',
        tracking=True,
        help="Commentaires de l'approbateur"
    )

    conditions = fields.Html(
        string='Conditions',
        tracking=True,
        help="Conditions à remplir pour l'approbation"
    )

    # =====================================================
    # SUIVI
    # =====================================================

    expiry_date = fields.Date(
        string="Date d'expiration",
        tracking=True,
        help="Date à laquelle l'approbation expire"
    )

    active = fields.Boolean(
        default=True,
        string='Actif'
    )

    # =====================================================
    # CONTRAINTES
    # =====================================================

    @api.constrains('approver_id', 'document_id')
    def _check_unique_approval(self):
        for record in self:
            existing = self.search([
                ('document_id', '=', record.document_id.id),
                ('approver_id', '=', record.approver_id.id),
                ('id', '!=', record.id),
                ('status', 'in', ['pending', 'approved'])
            ])
            if existing:
                raise ValidationError(_("Cet approbateur a déjà une demande en attente ou approuvée pour ce document."))

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_approve(self):
        """Approuve le document"""
        self.ensure_one()
        self.status = 'approved'
        # Mettre à jour le document si nécessaire
        if self.document_id.state in ['review', 'approval']:
            self.document_id.action_approve()
        return True

    def action_reject(self):
        """Rejette le document"""
        self.ensure_one()
        self.status = 'rejected'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Document rejeté'),
            'res_model': 'risk.document',
            'view_mode': 'form',
            'res_id': self.document_id.id,
            'target': 'current',
        }

    def action_conditionnal_approve(self):
        """Approbation conditionnelle"""
        self.ensure_one()
        self.status = 'conditionnal'
        return True

    def action_reset_to_pending(self):
        """Remet en attente"""
        self.ensure_one()
        self.status = 'pending'
        return True