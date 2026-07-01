from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskDocumentVersionWizard(models.TransientModel):
    _name = 'risk.document.version.wizard'
    _description = 'Assistant de création de version'

    document_id = fields.Many2one(
        'risk.document',
        string='Document',
        required=True
    )

    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Fichier',
        required=True,
        help="Sélectionnez le fichier à ajouter comme nouvelle version"
    )

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

    version_type = fields.Selection([
        ('initial', 'Version initiale'),
        ('major', 'Mise à jour majeure'),
        ('minor', 'Mise à jour mineure'),
        ('correction', 'Correction'),
        ('review', 'Révision'),
    ], string='Type de version', default='minor', required=True)

    changelog = fields.Text(
        string="Journal des modifications",
        required=True
    )

    effective_date = fields.Date(
        string="Date d'entrée en vigueur",
        default=fields.Date.today
    )

    def action_create_version(self):
        """Crée la nouvelle version"""
        self.ensure_one()

        # Calculer la nouvelle version
        if self.version_type == 'major':
            major = self.version_major + 1
            minor = 0
        else:
            major = self.version_major
            minor = self.version_minor + 1

        # Créer la version
        version = self.env['risk.document.version'].create({
            'document_id': self.document_id.id,
            'version_major': major,
            'version_minor': minor,
            'version_type': self.version_type,
            'attachment_id': self.attachment_id.id,
            'changelog': self.changelog,
            'effective_date': self.effective_date,
            'author_id': self.env.user.employee_id.id or False,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Version créée',
            'res_model': 'risk.document.version',
            'view_mode': 'form',
            'res_id': version.id,
            'target': 'current',
        }