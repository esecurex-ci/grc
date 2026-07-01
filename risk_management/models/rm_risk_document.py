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

    name = fields.Char(string="Title", required=True, tracking=True, translate=True, index=True)
    code = fields.Char(string="Code", required=True, copy=False, tracking=True, index=True)
    reference = fields.Char(string="Reference", tracking=True, index=True)

    category_id = fields.Many2one(
        "risk.document.category",
        string="Category",
        required=True,
        tracking=True,
        index=True,
        ondelete="restrict",
    )

    document_type = fields.Selection([
        ("policy", "Policy"),
        ("procedure", "Procedure"),
        ("standard", "Standard"),
        ("guideline", "Guideline"),
        ("manual", "Manual"),
        ("instruction", "Instruction"),
        ("template", "Template"),
        ("form", "Form"),
        ("register", "Register"),
        ("record", "Record"),
    ], string="Document Type", default="policy", required=True, tracking=True, index=True)

    process_id = fields.Many2one("risk.process", string="Business Process", tracking=True, index=True,
                                 ondelete="restrict")
    owner_id = fields.Many2one("hr.employee", string="Document Owner", tracking=True, index=True)
    author_id = fields.Many2one("hr.employee", string="Author", tracking=True, index=True)
    reviewer_id = fields.Many2one("hr.employee", string="Reviewer", tracking=True, index=True)
    approver_id = fields.Many2one("hr.employee", string="Approver", tracking=True, index=True)

    summary = fields.Char(string="Summary", translate=True)
    description = fields.Html(string="Description", translate=True)
    objective = fields.Html(string="Objective", translate=True)
    scope = fields.Html(string="Scope", translate=True)
    content = fields.Html(string="Content", translate=True)

    confidentiality = fields.Selection([
        ("public", "Public"),
        ("internal", "Internal"),
        ("confidential", "Confidential"),
        ("restricted", "Restricted"),
        ("secret", "Secret"),
    ], default="internal", tracking=True, required=True)

    language = fields.Selection([
        ("fr", "Français"),
        ("en", "English"),
    ], default="fr", required=True)

    keywords = fields.Char()
    tags = fields.Many2many("risk.tag", string="Tags")

    # =====================================================
    # RELATIONS GRC (AJOUT - pour la vue)
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
        string="Attachments",
    )

    attachment_count = fields.Integer(
        compute="_compute_attachment_count",
        store=True,
        string="Nombre de documents joints"
    )

    # =====================================================
    # VERSION MANAGEMENT
    # =====================================================

    version_major = fields.Integer(string="Major Version", default=1, tracking=True)
    version_minor = fields.Integer(string="Minor Version", default=0, tracking=True)
    version_label = fields.Char(compute="_compute_version_label", store=True)
    current_version_id = fields.Many2one("risk.document.version", string="Current Version", readonly=True, copy=False)
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
            ("draft", "Draft"),
            ("preparation", "In Preparation"),
            ("review", "Under Review"),
            ("approval", "Pending Approval"),
            ("approved", "Approved"),
            ("published", "Published"),
            ("obsolete", "Obsolete"),
            ("archived", "Archived"),
        ],
        default="draft",
        tracking=True,
        index=True
    )

    is_current = fields.Boolean(
        default=False,
        string="Version actuelle",
        help="Indique si ce document est la version actuelle"
    )

    # =====================================================
    # DOCUMENT LIFECYCLE
    # =====================================================

    creation_date = fields.Date(default=fields.Date.today, readonly=True)
    effective_date = fields.Date(tracking=True)
    approval_date = fields.Date(tracking=True)
    publication_date = fields.Date(tracking=True)
    next_review_date = fields.Date(tracking=True)
    expiry_date = fields.Date(tracking=True)
    archive_date = fields.Date(tracking=True)
    destruction_date = fields.Date(tracking=True)

    # =====================================================
    # REVIEW MANAGEMENT
    # =====================================================

    review_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semiannual", "Semi Annual"),
            ("annual", "Annual"),
            ("biennial", "Every 2 Years"),
            ("triennial", "Every 3 Years"),
        ],
        default="annual",
        tracking=True
    )

    review_ids = fields.One2many("risk.document.review", "document_id", string="Reviews")
    last_review_date = fields.Date(compute="_compute_last_review")

    review_status = fields.Selection(
        [
            ("ok", "Up To Date"),
            ("due", "Review Due"),
            ("overdue", "Overdue"),
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

    approval_ids = fields.One2many("risk.document.approval", "document_id", string="Approvals")
    approval_required = fields.Boolean(default=True)
    approval_level = fields.Selection(
        [
            ("single", "Single Approval"),
            ("double", "Double Approval"),
            ("committee", "Committee"),
        ],
        default="single"
    )

    # =====================================================
    # DISTRIBUTION
    # =====================================================

    distribution_ids = fields.One2many("risk.document.distribution", "document_id")
    mandatory_read = fields.Boolean(default=False)
    mandatory_training = fields.Boolean(default=False)

    # =====================================================
    # DOCUMENT HEALTH
    # =====================================================

    document_health_score = fields.Float(
        compute="_compute_document_health",
        store=True,
        digits=(16, 2)
    )

    health_level = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("warning", "Warning"),
            ("critical", "Critical"),
        ],
        compute="_compute_document_health",
        store=True
    )

    # =====================================================
    # OBSOLETE / ARCHIVE
    # =====================================================

    obsolete_reason = fields.Text()
    archive_reason = fields.Text()

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