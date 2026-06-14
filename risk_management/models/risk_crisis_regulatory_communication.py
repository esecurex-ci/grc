from odoo import models, fields


class RiskCrisisRegulatoryCommunication(models.Model):
    _name = 'risk.crisis.regulatory.communication'
    _description = 'Regulatory Communication'
    _inherit = ['mail.thread']
    _rec_name = 'name'
    _order = 'communication_date desc'

    name = fields.Char(
        string='Communication Title',
        required=True,
        tracking=True
    )

    # ⬇️ CHAMP OBLIGATOIRE POUR LA RELATION ⬇️
    crisis_id = fields.Many2one(
        'risk.crisis',
        string='Crisis',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    communication_date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )

    direction = fields.Selection(
        [
            ('incoming', 'Incoming'),
            ('outgoing', 'Outgoing')
        ],
        string='Direction',
        default='outgoing',
        required=True,
        tracking=True
    )

    authority = fields.Char(
        string='Regulatory Authority',
        required=True,
        tracking=True
    )

    reference = fields.Char(
        string='Reference Number',
        tracking=True
    )

    subject = fields.Char(
        string='Subject',
        required=True,
        tracking=True
    )

    content = fields.Html(
        string='Content',
        required=True
    )

    response_date = fields.Datetime(
        string='Response Date',
        tracking=True
    )

    response_content = fields.Html(
        string='Response Content'
    )

    responsible_id = fields.Many2one(
        'hr.employee',
        string='Responsible',
        tracking=True
    )

    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('sent', 'Sent'),
            ('received', 'Received'),
            ('answered', 'Answered'),
            ('closed', 'Closed')
        ],
        string='Status',
        default='draft',
        tracking=True
    )

    urgency = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('urgent', 'Urgent')
        ],
        string='Urgency',
        default='medium',
        tracking=True
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments'
    )

    notes = fields.Html(
        string='Notes'
    )

    # Méthodes d'action
    def action_send(self):
        """Marquer comme envoyé"""
        for record in self:
            record.status = 'sent'
            record.communication_date = fields.Datetime.now()

    def action_mark_received(self):
        """Marquer comme reçu"""
        for record in self:
            record.status = 'received'

    def action_mark_answered(self):
        """Marquer comme répondu"""
        for record in self:
            record.status = 'answered'
            record.response_date = fields.Datetime.now()

    def action_close(self):
        """Fermer la communication"""
        for record in self:
            record.status = 'closed'