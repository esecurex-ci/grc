from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskDocumentCategory(models.Model):
    _name = 'risk.document.category'
    _description = 'Catégorie de document de gouvernance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code, name'
    _rec_name = 'name'

    # =====================================================
    # INFORMATIONS GÉNÉRALES
    # =====================================================

    name = fields.Char(
        string='Nom',
        required=True,
        tracking=True,
        translate=True
    )

    code = fields.Char(
        string='Code',
        required=True,
        tracking=True,
        index=True
    )

    description = fields.Html(
        string='Description',
        translate=True,
        help="Description détaillée de la catégorie de documents"
    )

    # =====================================================
    # HIÉRARCHIE
    # =====================================================

    parent_id = fields.Many2one(
        'risk.document.category',
        string='Catégorie parente',
        ondelete='restrict',
        index=True,
        help="Catégorie parente dans la hiérarchie"
    )

    child_ids = fields.One2many(
        'risk.document.category',
        'parent_id',
        string='Sous-catégories'
    )

    child_count = fields.Integer(
        compute='_compute_child_count',
        store=True,
        string='Nombre de sous-catégories'
    )

    # =====================================================
    # STATISTIQUES
    # =====================================================

    document_count = fields.Integer(
        compute='_compute_document_count',
        store=True,
        string="Nombre de documents"
    )

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Décochez pour désactiver cette catégorie"
    )

    # =====================================================
    # COMPTES RENDUS
    # =====================================================

    @api.depends('child_ids')
    def _compute_child_count(self):
        for record in self:
            record.child_count = len(record.child_ids)

    @api.depends('name')
    def _compute_document_count(self):
        for record in self:
            record.document_count = self.env['risk.document'].search_count([
                ('category_id', '=', record.id),
                ('active', '=', True)
            ])

    # =====================================================
    # CONTRAINTES
    # =====================================================

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError(_("Le code '%s' est déjà utilisé par une autre catégorie.") % record.code)

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for record in self:
            if record.parent_id and record.parent_id.id == record.id:
                raise ValidationError(_("Une catégorie ne peut pas être sa propre catégorie parente."))

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_view_documents(self):
        """Ouvre la liste des documents de cette catégorie"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents - %s') % self.name,
            'res_model': 'risk.document',
            'view_mode': 'tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }

    def action_toggle_active(self):
        """Active ou désactive la catégorie"""
        self.ensure_one()
        self.active = not self.active
        return True


class RiskDocumentCategoryWizard(models.TransientModel):
    """Assistant pour créer rapidement une catégorie"""
    _name = 'risk.document.category.wizard'
    _description = 'Assistant de création de catégorie'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Html(string='Description')
    parent_id = fields.Many2one('risk.document.category', string='Catégorie parente')

    def action_create_category(self):
        """Crée la catégorie"""
        self.ensure_one()
        category = self.env['risk.document.category'].create({
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'parent_id': self.parent_id.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': _('Catégorie créée'),
            'res_model': 'risk.document.category',
            'view_mode': 'form',
            'res_id': category.id,
            'target': 'current',
        }