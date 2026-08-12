from odoo import models, fields, api


class RiskAuditFinding(models.Model):
    _name = 'risk.audit.finding'
    _description = "Constat d'audit"
    _inherit = ['mail.thread']

    # ⚠️ Champ 'readonly' avec default='New' mais sans séquence assignée à la
    # création (contrairement à risk.audit, qui a un create() dédié) : la
    # référence restait littéralement "New" pour toujours. Voir create()
    # ci-dessous et seq_risk_audit_finding dans data/sequence.xml.
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

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'risk.audit.finding'
                )
        return super().create(vals_list)
