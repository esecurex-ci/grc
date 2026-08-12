from odoo import models, fields, api


class RiskAudit(models.Model):
    _name = 'risk.audit'
    _description = 'Audit Mission'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        readonly=True,
        default='New'
    )

    title = fields.Char(
        required=True
    )

    plan_id = fields.Many2one(
        'risk.audit.plan'
    )

    audit_type = fields.Selection(
        [
            ('internal', 'Internal Audit'),
            ('external', 'External Audit'),
            ('regulator', 'Regulator Audit'),
            ('it', 'IT Audit')
        ],
        required=True
    )

    process_ids = fields.Many2many(
        'risk.process'
    )

    organization_ids = fields.Many2many(
        'risk.organization'
    )

    start_date = fields.Date()

    end_date = fields.Date()

    lead_auditor_id = fields.Many2one(
        'hr.employee'
    )

    objective = fields.Html()

    scope = fields.Html()

    # ⚠️ 'state' était un simple champ éditable dans le corps du formulaire :
    # n'importe qui pouvait faire passer une mission directement de 'draft' à
    # 'closed' en sautant les étapes de terrain/rédaction. Ajout de
    # tracking=True + de méthodes action_* explicites (voir plus bas),
    # utilisées désormais par un statusbar dans risk_audit_views.xml — même
    # traitement que celui déjà appliqué à risk.audit.plan / risk.bcp.plan /
    # risk.drp.plan / risk.exercise dans ce module.
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('planning', 'Planning'),
            ('fieldwork', 'Fieldwork'),
            ('reporting', 'Reporting'),
            ('closed', 'Closed')
        ],
        default='draft',
        tracking=True
    )

    finding_ids = fields.One2many(
        'risk.audit.finding',
        'audit_id'
    )

    finding_count = fields.Integer(
        compute='_compute_finding_count'
    )

    # ✅ Périmètre d'audit structuré (risk.audit.scope) — le modèle et ses
    # vues existaient déjà mais n'étaient reliés à aucune action/menu ni à la
    # fiche Mission : impossible de les créer/consulter depuis l'interface.
    scope_ids = fields.One2many(
        'risk.audit.scope',
        'audit_id',
        string='Éléments du périmètre'
    )

    scope_count = fields.Integer(
        compute='_compute_scope_count'
    )

    attachment_ids = fields.Many2many(
        'ir.attachment'
    )

    @api.depends('finding_ids')
    def _compute_finding_count(self):
        for rec in self:
            rec.finding_count = len(
                rec.finding_ids
            )

    @api.depends('scope_ids')
    def _compute_scope_count(self):
        for rec in self:
            rec.scope_count = len(
                rec.scope_ids
            )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('name', 'New') == 'New':

                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'risk.audit'
                )

        return super().create(vals_list)

    def action_view_findings(self):
        """Ouvre la vue des constats liés à cet audit.

        ⚠️ Corrigé : pointait vers 'risk.finding' (modèle inexistant dans ce
        module — le bon modèle est 'risk.audit.finding') avec un view_mode
        'tree,form' (alias obsolète ; ce module utilise 'list,form' partout
        ailleurs). Le bouton stat "Constats" de la fiche Mission provoquait
        donc une erreur au clic."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Constats',
            'res_model': 'risk.audit.finding',
            'view_mode': 'list,form',
            'domain': [('audit_id', '=', self.id)],
            'context': {'default_audit_id': self.id},
        }

    def action_view_scopes(self):
        """Ouvre le périmètre structuré (risk.audit.scope) de cette mission."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Périmètre',
            'res_model': 'risk.audit.scope',
            'view_mode': 'list,form',
            'domain': [('audit_id', '=', self.id)],
            'context': {'default_audit_id': self.id},
        }

    # ------------------------------------------------------------------
    # ✅ Workflow explicite de la Mission (voir commentaire sur le champ
    # 'state' ci-dessus). Chaque transition ne fait avancer/reculer le
    # statut que d'une étape, et 'action_reset_draft' permet de rouvrir une
    # mission (correction d'une erreur de saisie) sans toucher aux constats/
    # recommandations déjà enregistrés.
    # ------------------------------------------------------------------

    def action_start_planning(self):
        for record in self:
            record.state = 'planning'
        return True

    def action_start_fieldwork(self):
        for record in self:
            record.state = 'fieldwork'
        return True

    def action_start_reporting(self):
        for record in self:
            record.state = 'reporting'
        return True

    def action_close(self):
        for record in self:
            record.state = 'closed'
        return True

    def action_reset_draft(self):
        for record in self:
            record.state = 'draft'
        return True
