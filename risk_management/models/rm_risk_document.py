from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta


class RiskDocument(models.Model):
    _name = "risk.document"
    _description = "Governance Document"
    _inherit = [
        "mail.thread",
        "mail.activity.mixin",
    ]
    _order = "code, version_major desc, version_minor desc"
    _check_company_auto = True

    # =====================================================
    # CHAMPS PRINCIPAUX
    # =====================================================

    name = fields.Char(string="Titre", required=True, tracking=True, translate=True, index=True)
    code = fields.Char(string="Code", required=True, copy=False, tracking=True, index=True)
    reference = fields.Char(string="Reference", tracking=True, index=True)

    category_id = fields.Many2one(
        "risk.document.category",
        string="Catégorie",
        required=True,
        tracking=True,
        index=True,
        ondelete="restrict",
    )

    document_type = fields.Selection([
        ("policy", "Polique"),
        ("procedure", "Procédure"),
        ("standard", "Standard"),
        ("guideline", "Ligne directrice"),
        ("manual", "Manuel"),
        ("instruction", "Instruction"),
        ("template", "Template"),
        ("form", "Form"),
        ("register", "Régistre"),
        ("record", "Record"),
    ], string="Type Document", default="policy", required=True, tracking=True, index=True)

    process_id = fields.Many2one("risk.process", string="Sous Processus", tracking=True, index=True,
                                 ondelete="restrict")

    # ✅ REMPLACEMENT des champs employés par des champs fonction
    owner_id = fields.Many2one(
        "risk.function",
        string="Propriétaire Document (Function)",
        tracking=True,
        index=True,
        ondelete="restrict",
        help="Fonction responsable de ce document"
    )

    author_id = fields.Many2one(
        "risk.function",
        string="Auteur (Function)",
        tracking=True,
        index=True,
        ondelete="restrict",
        help="Fonction auteur de ce document"
    )

    reviewer_id = fields.Many2one(
        "risk.function",
        string="Chargé de réviser (Function)",
        tracking=True,
        index=True,
        ondelete="restrict",
        help="Fonction chargée de la revue de ce document"
    )

    approver_id = fields.Many2one(
        "risk.function",
        string="Validateur (Function)",
        tracking=True,
        index=True,
        ondelete="restrict",
        help="Fonction chargée de l'approbation de ce document"
    )

    # ✅ CHAMPS EMPLOYÉS (pour information - optionnels)
    # Ces champs peuvent être utilisés pour des informations supplémentaires
    owner_employee_id = fields.Many2one(
        "hr.employee",
        string="Auteur (Employé)",
        tracking=True,
        index=True,
        help="Employé responsable (information supplémentaire)"
    )

    author_employee_id = fields.Many2one(
        "hr.employee",
        string="Auteur (Employé)",
        tracking=True,
        index=True,
        help="Employé auteur (information supplémentaire)"
    )

    # Noms des fonctions (pour l'affichage)
    owner_function_name = fields.Char(
        related='owner_id.complete_name',
        string="Fonction de Propriétaire",
        store=True
    )
    author_function_name = fields.Char(
        related='author_id.complete_name',
        string="Function de l'Auteur",
        store=True
    )
    reviewer_function_name = fields.Char(
        related='reviewer_id.complete_name',
        string="Function de Révision",
        store=True
    )
    approver_function_name = fields.Char(
        related='approver_id.complete_name',
        string="Function de Validateur",
        store=True
    )

    summary = fields.Char(string="Résumé", translate=True)
    description = fields.Html(string="Description", translate=True)
    objective = fields.Html(string="Objectif", translate=True)
    scope = fields.Html(string="Périmètre", translate=True)
    content = fields.Html(string="Contenu", translate=True)

    confidentiality = fields.Selection([
        ("public", "Publique"),
        ("internal", "Interne"),
        ("confidential", "Confidentiel"),
        ("restricted", "Limité"),
        ("secret", "Secret"),
    ], default="internal", tracking=True, required=True, string="Niveau de confidentialité")

    language = fields.Selection([
        ("fr", "Français"),
        ("en", "English"),
    ], default="fr", required=True, srting="Langue")

    keywords = fields.Char()
    tags = fields.Many2many("risk.tag", string="Tags")

    # =====================================================
    # RELATIONS GRC
    # =====================================================

    risk_ids = fields.Many2many(
        'risk.risk',
        string='Risques couverts',
        help="Risques que ce document aide à mitiger"
    )

    control_ids = fields.Many2many(
        'risk.control',
        string='Contrôles associés',
        help="Contrôles associés à ce document"
    )

    regulation_ids = fields.Many2many(
        'risk.regulation',
        string='Réglementations liées',
        help="Réglementations liées à ce document"
    )

    # =====================================================
    # ACTIVE
    # =====================================================

    active = fields.Boolean(
        default=True,
        string='Actif',
        help="Décochez pour désactiver ce document"
    )

    # =====================================================
    # ATTACHMENTS
    # =====================================================

    attachment_ids = fields.Many2many(
        "ir.attachment",
        "risk_document_attachment_rel",
        "document_id",
        "attachment_id",
        string="Pièces jointes",
    )

    attachment_count = fields.Integer(
        compute="_compute_attachment_count",
        store=True,
        string="Nombre de documents joints"
    )

    # =====================================================
    # VERSION MANAGEMENT
    # =====================================================

    version_major = fields.Integer(string="Version Majeure", default=1, tracking=True)
    version_minor = fields.Integer(string="Version Mineure", default=0, tracking=True)
    version_label = fields.Char(compute="_compute_version_label", store=True, string="Version")
    current_version_id = fields.Many2one("risk.document.version", string="Version Actuelle", readonly=True, copy=False)
    version_ids = fields.One2many("risk.document.version", "document_id", string="Versions")

    # =====================================================
    # STATISTIQUES
    # =====================================================

    version_count = fields.Integer(
        compute="_compute_statistics",
        store=True,
        string="Nombre de versions"
    )

    review_count = fields.Integer(
        compute="_compute_statistics",
        store=True,
        string="Nombre de revues"
    )

    approval_count = fields.Integer(
        compute="_compute_statistics",
        store=True,
        string="Nombre d'approbations"
    )

    distribution_count = fields.Integer(
        compute="_compute_statistics",
        store=True,
        string="Nombre de distributions"
    )

    reader_count = fields.Integer(
        compute="_compute_statistics",
        store=True,
        string="Nombre de lecteurs"
    )

    pending_reader_count = fields.Integer(
        compute="_compute_statistics",
        store=True,
        string="Lecteurs en attente"
    )

    read_rate = fields.Float(
        compute="_compute_read_rate",
        store=True,
        digits=(16, 2),
        string="Taux de lecture"
    )

    # =====================================================
    # DOCUMENT WORKFLOW
    # =====================================================

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("preparation", "En Préparation"),
            ("review", "En Révision"),
            ("approval", "En Validation"),
            ("approved", "Validé"),
            ("published", "Publié"),
            ("obsolete", "Obsolete"),
            ("archived", "Archivé"),
        ],
        default="draft",
        tracking=True,
        index=True,
        string='Statut'
    )

    is_current = fields.Boolean(
        default=False,
        string="Version actuelle",
        help="Indique si ce document est la version actuelle"
    )

    # =====================================================
    # DOCUMENT LIFECYCLE
    # =====================================================

    creation_date = fields.Date(default=fields.Date.today, readonly=True, string="Date de création")
    effective_date = fields.Date(tracking=True, string="Date d'effet")
    approval_date = fields.Date(tracking=True, string="Date d'approbation")
    publication_date = fields.Date(tracking=True, string="Date de publication")
    next_review_date = fields.Date(tracking=True, string="Date de la prochaine révision")
    expiry_date = fields.Date(tracking=True, string="Date d'expiration")
    archive_date = fields.Date(tracking=True, string="Date d'archivage")
    destruction_date = fields.Date(tracking=True, string="Date de destruction")

    # =====================================================
    # REVIEW MANAGEMENT
    # =====================================================

    review_frequency = fields.Selection(
        [
            ("monthly", "Mensuelle"),
            ("quarterly", "Trimestrielle"),
            ("semiannual", "Semi-Annuel"),
            ("annual", "Annuelle"),
            ("biennial", "Biénnialle"),
            ("triennial", "Triénnialle"),
        ],
        default="annual",
        tracking=True,
        string="Fréquence de révision"
    )

    review_ids = fields.One2many("risk.document.review", "document_id", string="Réviseur")
    last_review_date = fields.Date(compute="_compute_last_review", string="Date de la dernière révision")

    review_status = fields.Selection(
        [
            ("ok", "A jour"),
            ("due", "A mettre à jour"),
            ("overdue", "En retard"),
        ],
        compute="_compute_review_status",
        store=True,
        string="Statut de révision"
    )

    review_due = fields.Boolean(
        compute="_compute_review_status",
        store=True,
        string="Révision due"
    )

    expired = fields.Boolean(
        compute="_compute_review_status",
        store=True,
        string="Expiré"
    )

    # =====================================================
    # APPROVAL
    # =====================================================

    approval_ids = fields.One2many("risk.document.approval", "document_id", string="Approuvé")
    approval_required = fields.Boolean(default=True, string="A approuver avant publication")
    approval_level = fields.Selection(
        [
            ("single", "Approbation Simple"),
            ("double", "Double Approbation"),
            ("committee", "Comité"),
        ],
        default="single",
        string="Niveau d'approbation"
    )

    # =====================================================
    # DISTRIBUTION
    # =====================================================

    distribution_ids = fields.One2many("risk.document.distribution", "document_id", string="Distribution")
    mandatory_read = fields.Boolean(default=False, string="Lecture obligatoire")
    mandatory_training = fields.Boolean(default=False, string="Formation obligatoire")

    # =====================================================
    # DOCUMENT HEALTH
    # =====================================================

    document_health_score = fields.Float(
        compute="_compute_document_health",
        store=True,
        digits=(16, 2),
        string="Score de santé"
    )

    health_level = fields.Selection(
        [
            ("excellent", "Excéllent"),
            ("good", "Bon"),
            ("warning", "Avertissement"),
            ("critical", "Critique"),
        ],
        compute="_compute_document_health",
        store=True,
        string="Niveau de santé"
    )

    # =====================================================
    # OBSOLETE / ARCHIVE
    # =====================================================

    obsolete_reason = fields.Text(string="Raison de l'obsolescence")
    archive_reason = fields.Text(string="Raison de l'archivage")

    image_128 = fields.Binary(string='Image', attachment=True, help='Image du document')
    color = fields.Integer(string='Color', help='Couleur pour l\'affichage en kanban')

    # =====================================================
    # NAME_GET
    # =====================================================

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}" if record.code else record.name
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        return self.search(domain + args, limit=limit).name_get()

    # =====================================================
    # COMPUTES
    # =====================================================

    @api.depends('version_major', 'version_minor')
    def _compute_version_label(self):
        for record in self:
            record.version_label = f"v{record.version_major}.{record.version_minor}"

    @api.depends('version_ids', 'review_ids', 'approval_ids', 'distribution_ids')
    def _compute_statistics(self):
        for record in self:
            record.version_count = len(record.version_ids)
            record.review_count = len(record.review_ids)
            record.approval_count = len(record.approval_ids)
            record.distribution_count = len(record.distribution_ids)
            record.reader_count = len(record.distribution_ids.filtered(lambda d: d.confirmed))
            record.pending_reader_count = len(record.distribution_ids.filtered(lambda d: not d.confirmed))

    @api.depends('review_ids.review_date')
    def _compute_last_review(self):
        for record in self:
            last = record.review_ids.sorted('review_date', reverse=True)[:1]
            record.last_review_date = last.review_date if last else False

    @api.depends('last_review_date', 'next_review_date')
    def _compute_review_status(self):
        today = fields.Date.today()
        for record in self:
            if not record.next_review_date:
                record.review_status = 'ok'
                record.review_due = False
                record.expired = False
            elif record.next_review_date < today:
                record.review_status = 'overdue'
                record.review_due = False
                record.expired = True
            elif record.next_review_date <= today + relativedelta(days=30):
                record.review_status = 'due'
                record.review_due = True
                record.expired = False
            else:
                record.review_status = 'ok'
                record.review_due = False
                record.expired = False

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    @api.depends('reader_count', 'distribution_count')
    def _compute_read_rate(self):
        for record in self:
            if record.distribution_count > 0:
                record.read_rate = (record.reader_count / record.distribution_count) * 100
            else:
                record.read_rate = 0

    @api.depends('state', 'review_status', 'version_count', 'read_rate')
    def _compute_document_health(self):
        for record in self:
            score = 100

            if record.state in ['archived', 'obsolete']:
                score -= 40
            elif record.state == 'draft':
                score -= 30
            elif record.state == 'review':
                score -= 15

            if record.review_status == 'overdue':
                score -= 25
            elif record.review_status == 'due':
                score -= 10

            if record.version_count == 0:
                score -= 20

            if record.read_rate < 50:
                score -= 20
            elif record.read_rate < 80:
                score -= 10

            record.document_health_score = max(0, score)

            if score >= 80:
                record.health_level = 'excellent'
            elif score >= 60:
                record.health_level = 'good'
            elif score >= 40:
                record.health_level = 'warning'
            else:
                record.health_level = 'critical'

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_submit_review(self):
        self.ensure_one()
        self.state = 'review'
        return True

    def action_approve(self):
        self.ensure_one()
        self.state = 'approved'
        self.approval_date = fields.Date.today()
        return True

    def action_publish(self):
        self.ensure_one()
        self.state = 'published'
        self.publication_date = fields.Date.today()
        if not self.effective_date:
            self.effective_date = fields.Date.today()
        return True

    def action_archive(self):
        self.ensure_one()
        self.state = 'archived'
        self.archive_date = fields.Date.today()
        self.active = False
        return True

    def action_obsolete(self):
        self.ensure_one()
        self.state = 'obsolete'
        self.active = False
        return True

    def action_create_version(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Nouvelle version - {self.name}',
            'res_model': 'risk.document.version',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_document_id': self.id,
                'default_version_major': self.version_major,
                'default_version_minor': self.version_minor + 1,
            },
        }

    def action_view_versions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Versions - {self.name}',
            'res_model': 'risk.document.version',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
        }

    def action_view_reviews(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Revues - {self.name}',
            'res_model': 'risk.document.review',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
        }

    def action_view_approvals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Approbations - {self.name}',
            'res_model': 'risk.document.approval',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
        }

    def action_view_distributions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Distributions - {self.name}',
            'res_model': 'risk.document.distribution',
            'view_mode': 'tree,form,kanban',
            'domain': [('document_id', '=', self.id)],
        }

    def action_view_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Documents joints - {self.name}',
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,tree,form',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }