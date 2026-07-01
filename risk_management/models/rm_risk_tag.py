from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskTag(models.Model):
    _name = 'risk.tag'
    _description = 'Tag / Étiquette'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category_id, name'
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
        tracking=True,
        index=True
    )

    description = fields.Html(
        string='Description',
        translate=True
    )

    # =====================================================
    # CATÉGORIE
    # =====================================================

    category_id = fields.Many2one(
        'risk.tag.category',
        string='Catégorie',
        ondelete='set null',
        index=True,
        help="Catégorie de tag pour organiser les étiquettes"
    )

    category_name = fields.Char(
        related='category_id.name',
        string='Catégorie',
        store=True
    )

    # =====================================================
    # COULEUR
    # =====================================================

    color = fields.Char(string='Couleur', default='#6c757d')

    color_hex = fields.Char(
        compute='_compute_color_hex',
        string='Couleur hexadécimale',
        store=False
    )

    # =====================================================
    # STATISTIQUES
    # =====================================================

    use_count = fields.Integer(
        compute='_compute_use_count',
        store=True,
        string="Nombre d'utilisations"
    )

    active = fields.Boolean(
        default=True,
        string='Actif'
    )

    # =====================================================
    # COMPTES RENDUS
    # =====================================================

    @api.depends('name')
    def _compute_use_count(self):
        """Compte le nombre d'utilisations du tag dans différents modèles"""
        for record in self:
            count = 0

            # Compter dans les documents de gouvernance
            count += self.env['risk.document'].search_count([
                ('tags', 'in', record.id),
                ('active', '=', True)
            ])

            # ❌ SUPPRIMÉ : risk.risk.tag_ids n'existe pas
            # Si vous voulez compter les utilisations dans risk.risk,
            # assurez-vous d'abord que le champ tag_ids existe
            # count += self.env['risk.risk'].search_count([
            #     ('tag_ids', 'in', record.id),
            #     ('active', '=', True)
            # ])

            record.use_count = count

    @api.depends('color')
    def _compute_color_hex(self):
        """Convertit l'index de couleur en code hexadécimal"""
        color_map = {
            0: '#6c757d',  # Gris
            1: '#dc3545',  # Rouge
            2: '#fd7e14',  # Orange
            3: '#ffc107',  # Jaune
            4: '#28a745',  # Vert
            5: '#17a2b8',  # Cyan
            6: '#1a237e',  # Bleu foncé
            7: '#6f42c1',  # Violet
            8: '#e83e8c',  # Rose
            9: '#20c997',  # Turquoise
            10: '#0d6efd',  # Bleu
            11: '#6610f2',  # Indigo
            12: '#d63384',  # Magenta
            13: '#198754',  # Vert foncé
            14: '#0dcaf0',  # Cyan clair
            15: '#adb5bd',  # Gris clair
        }
        for record in self:
            record.color_hex = color_map.get(record.color, '#6c757d')

    # =====================================================
    # CONTRAINTES
    # =====================================================

    @api.constrains('name')
    def _check_name(self):
        for record in self:
            if self.search([('name', '=', record.name), ('id', '!=', record.id)]):
                raise ValidationError(_("Un tag avec le nom '%s' existe déjà.") % record.name)

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_view_documents(self):
        """Ouvre la liste des documents utilisant ce tag"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents - %s') % self.name,
            'res_model': 'risk.document',
            'view_mode': 'tree,form',
            'domain': [('tags', 'in', self.id)],
        }

    def action_toggle_active(self):
        """Active ou désactive le tag"""
        self.ensure_one()
        self.active = not self.active
        return True


class RiskTagCategory(models.Model):
    _name = 'risk.tag.category'
    _description = 'Catégorie de tag'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom',
        required=True,
        tracking=True,
        translate=True
    )

    code = fields.Char(
        string='Code',
        tracking=True,
        index=True
    )

    description = fields.Html(
        string='Description',
        translate=True
    )

    tag_ids = fields.One2many(
        'risk.tag',
        'category_id',
        string='Tags'
    )

    tag_count = fields.Integer(
        compute='_compute_tag_count',
        string="Nombre de tags"
    )

    active = fields.Boolean(
        default=True,
        string='Actif'
    )

    @api.depends('tag_ids')
    def _compute_tag_count(self):
        for record in self:
            record.tag_count = len(record.tag_ids)

    def action_view_tags(self):
        """Ouvre la liste des tags de cette catégorie"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Tags - %s') % self.name,
            'res_model': 'risk.tag',
            'view_mode': 'tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }

    def action_view_risks(self):
        """Ouvre la liste des risques utilisant ce tag"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Risques - %s') % self.name,
            'res_model': 'risk.risk',
            'view_mode': 'tree,form',
            'domain': [('tag_ids', 'in', self.id)],
        }