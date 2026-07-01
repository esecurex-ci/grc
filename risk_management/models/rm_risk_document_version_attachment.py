from odoo import api, fields, models


class RiskDocumentVersionAttachment(models.Model):
    _name = 'risk.document.version.attachment'
    _description = 'Version document avec attachement'
    _order = 'document_id, version_major desc, version_minor desc'
    _rec_name = 'version_label'

    # =====================================================
    # RELATIONS
    # =====================================================

    document_id = fields.Many2one(
        'risk.document',
        string='Document',
        required=True,
        ondelete='cascade'
    )

    version_id = fields.Many2one(
        'risk.document.version',
        string='Version associée',
        ondelete='cascade',
        help="Version du document correspondante"
    )

    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Fichier',
        required=True,
        ondelete='restrict'
    )

    # =====================================================
    # INFORMATIONS DE VERSION
    # =====================================================

    version_major = fields.Integer(
        string='Version majeure',
        required=True,
        default=1
    )

    version_minor = fields.Integer(
        string='Version mineure',
        required=True,
        default=0
    )

    version_label = fields.Char(
        compute='_compute_version_label',
        store=True,
        string='Version'
    )

    @api.depends('version_major', 'version_minor')
    def _compute_version_label(self):
        for record in self:
            record.version_label = f"v{record.version_major}.{record.version_minor}"

    # =====================================================
    # MÉTADONNÉES
    # =====================================================

    author_id = fields.Many2one(
        'hr.employee',
        string='Auteur'
    )

    creation_date = fields.Date(
        default=fields.Date.today,
        string='Date de création',
        readonly=True
    )

    changelog = fields.Text(
        string="Journal des modifications"
    )

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_download(self):
        """Télécharge le fichier"""
        self.ensure_one()
        return self.attachment_id.action_download()