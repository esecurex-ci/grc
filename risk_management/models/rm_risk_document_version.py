from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskDocumentVersion(models.Model):
    _name = 'risk.document.version'
    _description = 'Version du document de gouvernance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'document_id, version_major desc, version_minor desc'
    _rec_name = 'version_label'

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
    # INFORMATIONS DE VERSION
    # =====================================================

    version_major = fields.Integer(
        string='Version majeure',
        required=True,
        default=1,
        tracking=True
    )

    version_minor = fields.Integer(
        string='Version mineure',
        required=True,
        default=0,
        tracking=True
    )

    version_label = fields.Char(
        compute='_compute_version_label',
        store=True,
        string='Version',
        index=True
    )

    version_type = fields.Selection([
        ('initial', 'Version initiale'),
        ('major', 'Mise à jour majeure'),
        ('minor', 'Mise à jour mineure'),
        ('correction', 'Correction'),
        ('review', 'Révision'),
        ('archived', 'Version archivée'),
    ], string='Type de version', default='initial', tracking=True)

    # =====================================================
    # CONTENU
    # =====================================================

    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Fichier',
        required=True,
        ondelete='restrict',
        help="Fichier attaché à cette version du document"
    )

    filename = fields.Char(
        related='attachment_id.name',
        string='Nom du fichier',
        store=True
    )

    file_size = fields.Integer(
        related='attachment_id.file_size',
        string='Taille (Ko)',
        store=True
    )

    changelog = fields.Text(
        string="Journal des modifications",
        help="Description des changements apportés dans cette version",
        tracking=True
    )

    summary = fields.Html(
        string="Résumé des modifications",
        help="Résumé détaillé des changements"
    )

    # =====================================================
    # MÉTADONNÉES
    # =====================================================

    author_id = fields.Many2one(
        'hr.employee',
        string='Auteur',
        tracking=True,
        help="Personne ayant créé cette version"
    )

    reviewer_id = fields.Many2one(
        'hr.employee',
        string='Relecteur',
        tracking=True,
        help="Personne ayant relu cette version"
    )

    approver_id = fields.Many2one(
        'hr.employee',
        string='Approbateur',
        tracking=True,
        help="Personne ayant approuvé cette version"
    )

    creation_date = fields.Date(
        default=fields.Date.today,
        string='Date de création',
        readonly=True
    )

    approval_date = fields.Date(
        string="Date d'approbation",
        tracking=True
    )

    effective_date = fields.Date(
        string="Date d'entrée en vigueur",
        tracking=True,
        help="Date à partir de laquelle cette version est applicable"
    )

    # =====================================================
    # STATUT
    # =====================================================

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('review', 'En relecture'),
        ('approved', 'Approuvée'),
        ('published', 'Publiée'),
        ('archived', 'Archivée'),
    ], string='Statut', default='draft', tracking=True, index=True)

    is_current = fields.Boolean(
        string='Version actuelle',
        default=False,
        help="Cochez si cette version est la version active du document"
    )

    is_obsolete = fields.Boolean(
        string='Obsolète',
        default=False,
        help="Cochez si cette version n'est plus valide"
    )

    # =====================================================
    # CALCULS
    # =====================================================

    @api.depends('version_major', 'version_minor')
    def _compute_version_label(self):
        for record in self:
            record.version_label = f"v{record.version_major}.{record.version_minor}"

    @api.constrains('version_major', 'version_minor')
    def _check_version(self):
        for record in self:
            if record.version_major < 0 or record.version_minor < 0:
                raise ValidationError("Les versions doivent être des nombres positifs.")
            if record.version_major == 0 and record.version_minor == 0:
                raise ValidationError("La version 0.0 n'est pas autorisée.")

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_download(self):
        """Télécharge le fichier attaché"""
        self.ensure_one()
        return self.attachment_id.action_download()

    def action_view_attachment(self):
        """Ouvre le fichier attaché"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fichier',
            'res_model': 'ir.attachment',
            'view_mode': 'form',
            'res_id': self.attachment_id.id,
        }

    def action_set_current(self):
        """Définit cette version comme version actuelle"""
        self.ensure_one()
        # Réinitialiser toutes les versions du document
        self.document_id.version_ids.write({'is_current': False})
        # Définir cette version comme actuelle
        self.write({'is_current': True})
        # Mettre à jour le document
        self.document_id.write({
            'current_version_id': self.id,
            'version_major': self.version_major,
            'version_minor': self.version_minor,
            'effective_date': self.effective_date or fields.Date.today(),
        })

    def action_archive(self):
        """Archive cette version"""
        self.ensure_one()
        self.write({
            'state': 'archived',
            'is_obsolete': True,
            'is_current': False,
        })

    def action_approve(self):
        """Approuve cette version"""
        self.ensure_one()
        self.write({
            'state': 'approved',
            'approval_date': fields.Date.today(),
        })

    def action_publish(self):
        """Publie cette version"""
        self.ensure_one()
        self.write({
            'state': 'published',
            'effective_date': self.effective_date or fields.Date.today(),
        })
        self.action_set_current()