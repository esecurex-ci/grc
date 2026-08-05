from odoo import models, fields


class RiskAuditFinding(models.Model):
    _name = 'risk.audit.finding'
    _description = "Constat d'audit"
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Référence',
        readonly=True,
        default='New'
    )

    audit_id = fields.Many2one(
        'risk.audit',
        string='Audit',
        required=True,
        ondelete='cascade'
    )

    title = fields.Char(
        string='Titre',
        required=True
    )

    description = fields.Html(string='Description')

    risk_id = fields.Many2one(
        'risk.risk',
        string='Risque'
    )

    control_id = fields.Many2one(
        'risk.control',
        string='Contrôle'
    )

    severity = fields.Selection(
        [
            ('low', 'Faible'),
            ('moderate', 'Modérée'),
            ('high', 'Élevée'),
            ('critical', 'Critique')
        ],
        string='Gravité',
        default='moderate'
    )

    root_cause = fields.Html(string='Cause racine')

    recommendation_ids = fields.One2many(
        'risk.audit.recommendation',
        'finding_id',
        string='Recommandations'
    )

    state = fields.Selection(
        [
            ('open', 'Ouvert'),
            ('in_progress', 'En cours'),
            ('closed', 'Clôturé')
        ],
        string='Statut',
        default='open'
    )
    regulation_ids = fields.Many2many(
        'risk.regulation',
        string='Réglementations'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Pièces jointes'
    )
    compliance_requirement_ids = fields.Many2many(
        'risk.compliance.requirement',
        string='Exigences de conformité'
    )
