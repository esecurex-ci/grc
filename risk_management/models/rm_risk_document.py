from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class RiskDocument(models.Model):
    _name = "risk.document"
    _description = "Governance Document"
    """_inherit = [
        "risk.grc.mixin",
        "mail.thread",
        "mail.activity.mixin",
        "image.mixin",
    ]"""

    _order = "code, version_major desc, version_minor desc"
    #_rec_name = "display_name"
    _check_company_auto = True

    name = fields.Char(string="Title",required=True,tracking=True, translate=True, index=True,)
    code = fields.Char(string="Code", required=True, copy=False,tracking=True,  index=True,)
    reference = fields.Char(string="Reference", tracking=True, index=True,)
    full_name = fields.Char(compute="_compute_display_name", store=True,index=True,)
    category_id = fields.Many2one(
        "risk.document.category",
        string="Category",
        required=True,
        tracking=True,
        index=True,
        ondelete="restrict",
    )
    document_type = fields.Selection([("policy", "Policy"), ("procedure", "Procedure"), ("standard", "Standard"),
            ("guideline", "Guideline"),("manual", "Manual"), ("instruction", "Instruction"), ("template", "Template"),
            ("form", "Form"), ("register", "Register"),("record", "Record"),
        ],
        string="Document Type",default="policy",required=True, tracking=True, index=True, )
    process_id = fields.Many2one("risk.process",string="Business Process", tracking=True, index=True, ondelete="restrict",)
    owner_id = fields.Many2one("hr.employee",string="Document Owner", tracking=True,index=True,)
    author_id = fields.Many2one("hr.employee",string="Author", tracking=True,index=True,)
    reviewer_id = fields.Many2one("hr.employee",string="Reviewer", tracking=True,index=True,)
    approver_id = fields.Many2one("hr.employee",string="Approver", tracking=True,index=True,)
    summary = fields.Char(string="Summary", translate=True,)
    description = fields.Html(string="Description", translate=True,)
    objective = fields.Html(string="Objective", translate=True,)
    scope = fields.Html(string="Scope", translate=True,)
    scope = fields.Html(string="Scope", translate=True,)
    confidentiality = fields.Selection([("public", "Public"), ("internal", "Internal"), ("confidential", "Confidential"),
            ("restricted", "Restricted"), ("secret", "Secret"),], default="internal", tracking=True, required=True, )
    language = fields.Selection([("fr", "Français"), ("en", "English"),],default="fr",required=True,)
    keywords = fields.Char()
    tags = fields.Many2many("risk.tag", string="Tags",)
    attachment_ids = fields.Many2many( "ir.attachment","risk_document_attachment_rel", "document_id","attachment_id",
        string="Attachments", )
    # =====================================================
    # VERSION MANAGEMENT
    # =====================================================
    version_major = fields.Integer( string="Major Version",default=1,tracking=True)
    version_minor = fields.Integer( string="Minor Version",default=0,tracking=True)
    version_label = fields.Char( string="Version", compute="_compute_version_label",store=True)
    current_version_id = fields.Many2one("risk.document.version", string="Current Version", readonly=True,  copy=False)
    version_ids = fields.One2many("risk.document.version", "document_id", string="Versions")
    version_count = fields.Integer( compute="_compute_statistics")

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
        ], default="annual", tracking=True)
    review_ids = fields.One2many("risk.document.review",
        "document_id", string="Reviews")
    review_count = fields.Integer(compute="_compute_statistics")
    last_review_date = fields.Date(compute="_compute_last_review")
    review_status = fields.Selection(
        [("ok", "Up To Date"),("due", "Review Due"),("overdue", "Overdue"),
        ], compute="_compute_review_status")
    # =====================================================
    # APPROVAL
    # =====================================================
    approval_ids = fields.One2many("risk.document.approval",
        "document_id",string="Approvals"
    )
    approval_count = fields.Integer(compute="_compute_statistics")
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
    distribution_ids = fields.One2many("risk.document.distribution",
        "document_id")
    distribution_count = fields.Integer(compute="_compute_statistics")
    mandatory_read = fields.Boolean(default=False)
    mandatory_training = fields.Boolean(default=False)
    # =====================================================
    # READ CONFIRMATION
    # =====================================================
    reader_count = fields.Integer(compute="_compute_statistics")
    pending_reader_count = fields.Integer(compute="_compute_statistics")
    read_rate = fields.Float(compute="_compute_read_rate", digits=(16, 2))
    # =====================================================
    # DOCUMENT HEALTH
    # =====================================================
    document_health_score = fields.Float(compute="_compute_document_health", digits=(16, 2), store=True)
    health_level = fields.Selection([("excellent", "Excellent"),("good", "Good"),("warning", "Warning"),("critical", "Critical"),
        ],
        compute="_compute_document_health",
        store=True
    )
    # =====================================================
    # KPIs
    # =====================================================
    review_due = fields.Boolean(compute="_compute_review_status")
    expired = fields.Boolean(compute="_compute_review_status")
    is_current = fields.Boolean(default=True)
    obsolete_reason = fields.Text()
    archive_reason = fields.Text()



