from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskDocumentDistribution(models.Model):
    _name = 'risk.document.distribution'
    _description = 'Distribution de document de gouvernance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'document_id, employee_id'

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

    employee_id = fields.Many2one(
        'hr.employee',
        string='Destinataire',
        required=True,
        tracking=True
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Département',
        tracking=True,
        help="Département du destinataire"
    )

    # =====================================================
    # SUIVI DE LECTURE
    # =====================================================

    read_date = fields.Date(
        string='Date de lecture',
        tracking=True
    )

    confirmed = fields.Boolean(
        string='Lecture confirmée',
        default=False,
        tracking=True
    )

    confirmation_date = fields.Date(
        string='Date de confirmation',
        tracking=True
    )

    # =====================================================
    # FORMATION
    # =====================================================

    training_completed = fields.Boolean(
        string='Formation effectuée',
        default=False,
        tracking=True
    )

    training_date = fields.Date(
        string='Date de formation',
        tracking=True
    )

    training_score = fields.Float(
        string='Score de formation',
        digits=(16, 2),
        tracking=True,
        help="Score obtenu à l'évaluation de la formation"
    )

    # =====================================================
    # COMMENTAIRES
    # =====================================================

    comments = fields.Html(
        string='Commentaires',
        tracking=True
    )

    # =====================================================
    # MÉTADONNÉES
    # =====================================================

    active = fields.Boolean(
        default=True,
        string='Actif'
    )

    # =====================================================
    # CONTRAINTES
    # =====================================================

    @api.constrains('employee_id', 'document_id')
    def _check_unique_distribution(self):
        for record in self:
            existing = self.search([
                ('document_id', '=', record.document_id.id),
                ('employee_id', '=', record.employee_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(_("Ce destinataire a déjà reçu ce document."))

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_confirm_read(self):
        """Confirme la lecture du document"""
        self.ensure_one()
        self.confirmed = True
        self.confirmation_date = fields.Date.today()
        return True

    def action_confirm_training(self):
        """Confirme la formation"""
        self.ensure_one()
        self.training_completed = True
        self.training_date = fields.Date.today()
        return True

    def action_send_reminder(self):
        """Envoie un rappel au destinataire"""
        self.ensure_one()
        # Logique d'envoi d'email
        return {
            'type': 'ir.actions.act_window',
            'name': _('Envoyer un rappel'),
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_composition_mode': 'comment',
                'default_partner_ids': [(4, self.employee_id.user_id.partner_id.id)],
                'default_subject': _('Rappel: Lecture du document %s') % self.document_id.name,
                'default_body': _(
                    "Bonjour,\n\nVeuillez prendre connaissance du document '%s'.\n\nMerci.") % self.document_id.name,
            },
        }