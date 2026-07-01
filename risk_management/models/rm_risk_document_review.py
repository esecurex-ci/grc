from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskDocumentReview(models.Model):
    _name = 'risk.document.review'
    _description = 'Revue de document de gouvernance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'review_date desc, document_id'
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

    # =====================================================
    # INFORMATIONS DE REVUE
    # =====================================================

    review_date = fields.Date(
        string='Date de la revue',
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    reviewer_id = fields.Many2one(
        'hr.employee',
        string='Relecteur',
        required=True,
        tracking=True
    )

    status = fields.Selection([
        ('planned', '📅 Planifiée'),
        ('in_progress', '🔄 En cours'),
        ('completed', '✅ Terminée'),
        ('cancelled', '❌ Annulée'),
    ], string='Statut', default='planned', tracking=True, index=True)

    # =====================================================
    # COMMENTAIRES ET CONCLUSIONS
    # =====================================================

    comments = fields.Html(
        string='Commentaires',
        tracking=True,
        help="Commentaires détaillés sur la revue"
    )

    findings = fields.Html(
        string='Constatations',
        tracking=True,
        help="Constats et observations lors de la revue"
    )

    recommendations = fields.Html(
        string='Recommandations',
        tracking=True,
        help="Recommandations issues de la revue"
    )

    action_plan = fields.Html(
        string="Plan d'action",
        tracking=True,
        help="Actions à mener suite à la revue"
    )

    # =====================================================
    # SUIVI
    # =====================================================

    next_review_date = fields.Date(
        string='Prochaine revue',
        tracking=True,
        help="Date proposée pour la prochaine revue"
    )

    review_period = fields.Selection([
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('semiannual', 'Semestrielle'),
        ('annual', 'Annuelle'),
        ('biennial', 'Bisanuelle'),
    ], string='Périodicité', tracking=True)

    # =====================================================
    # MÉTADONNÉES
    # =====================================================

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'risk_document_review_attachment_rel',
        'review_id',
        'attachment_id',
        string='Pièces jointes'
    )

    active = fields.Boolean(
        default=True,
        string='Actif'
    )

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_start_review(self):
        """Démarre la revue"""
        self.ensure_one()
        self.status = 'in_progress'
        return True

    def action_complete_review(self):
        """Termine la revue"""
        self.ensure_one()
        self.status = 'completed'
        return {
            'type': 'ir.actions.act_window',
            'name': _('Revue terminée'),
            'res_model': 'risk.document.review',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'current',
        }

    def action_cancel_review(self):
        """Annule la revue"""
        self.ensure_one()
        self.status = 'cancelled'
        return True

    def action_create_next_review(self):
        """Crée la prochaine revue planifiée"""
        self.ensure_one()
        if not self.next_review_date:
            raise ValidationError(_("Veuillez définir une date pour la prochaine revue."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Créer une nouvelle revue'),
            'res_model': 'risk.document.review',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_id': self.document_id.id,
                'default_review_date': self.next_review_date,
                'default_reviewer_id': self.reviewer_id.id,
                'default_review_period': self.review_period,
            },
        }