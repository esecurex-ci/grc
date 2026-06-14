from odoo import models, fields, api


class RiskCrisis(models.Model):
    _name = 'risk.crisis'
    _description = 'Crisis Management'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        readonly=True,
        default='New'
    )

    title = fields.Char(
        required=True,
        tracking=True
    )

    scenario_id = fields.Many2one(
        'risk.crisis.scenario'
    )

    incident_id = fields.Many2one(
        'risk.incident'
    )

    declaration_date = fields.Datetime(
        default=fields.Datetime.now
    )

    start_date = fields.Datetime()

    end_date = fields.Datetime()

    resolution_date = fields.Datetime(
        string='Resolution Date'
    )

    crisis_level = fields.Selection(
        [
            ('minor', 'Minor'),
            ('major', 'Major'),
            ('critical', 'Critical')
        ],
        default='major'
    )

    crisis_manager_id = fields.Many2one(
        'hr.employee',
        string='Crisis Manager'
    )

    description = fields.Html()

    impact = fields.Html()

    state = fields.Selection([
        ('declared', 'Declared'),
        ('activated', 'Activated'),
        ('managed', 'Managed'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], string='Status', default='declared', tracking=True)

    team_ids = fields.One2many(
        'risk.crisis.member',
        'crisis_id'
    )

    action_ids = fields.One2many(
        'risk.crisis.action',
        'crisis_id'
    )

    communication_ids = fields.One2many(
        'risk.crisis.communication',
        'crisis_id'
    )

    decision_ids = fields.One2many(
        'risk.crisis.decision',
        'crisis_id'
    )

    log_ids = fields.One2many(
        'risk.crisis.log',
        'crisis_id'
    )

    rex_id = fields.One2many(
        'risk.crisis.rex',
        'crisis_id'
    )

    regulator_notification_required = fields.Boolean()
    regulator_notification_date = fields.Datetime()
    regulator_reference = fields.Char()

    crisis_committee_meeting_ids = fields.One2many(
        'risk.crisis.committee.meeting',
        'crisis_id',
        string='Committee Meetings'
    )

    # Champs calculés
    meeting_count = fields.Integer(
        compute='_compute_meeting_count'
    )
    team_count = fields.Integer(
        compute='_compute_statistics'
    )
    action_count = fields.Integer(
        compute='_compute_statistics'
    )
    communication_count = fields.Integer(
        compute='_compute_statistics'
    )
    decision_count = fields.Integer(
        compute='_compute_statistics'
    )
    log_count = fields.Integer(
        compute='_compute_statistics'
    )
    rex_count = fields.Integer(
        compute='_compute_statistics'
    )

    # =====================================================
    # MÉTHODES DE WORKFLOW (CORRIGÉES)
    # =====================================================

    def action_activate(self):
        """Activer la crise"""
        for record in self:
            record.state = 'activated'
            if not record.start_date:
                record.start_date = fields.Datetime.now()
        return True

    def action_manage(self):
        """Passer la crise en mode gestion active"""
        for record in self:
            record.state = 'managed'
        return True

    def action_resolve(self):
        """Résoudre la crise"""
        for record in self:
            record.state = 'resolved'
            if not record.resolution_date:
                record.resolution_date = fields.Datetime.now()
        return True

    def action_close(self):
        """Fermer la crise"""
        for record in self:
            record.state = 'closed'
            if not record.end_date:
                record.end_date = fields.Datetime.now()
        return True

    def action_draft(self):
        """Remettre en déclarée"""
        for record in self:
            record.state = 'declared'
        return True

    # =====================================================
    # MÉTHODES DE VUE
    # =====================================================

    def action_view_meetings(self):
        """Ouvre la vue des réunions"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Committee Meetings',
            'res_model': 'risk.crisis.committee.meeting',
            'view_mode': 'tree,form',
            'domain': [('crisis_id', '=', self.id)],
            'context': {'default_crisis_id': self.id},
        }

    def action_view_actions(self):
        """Ouvre la vue des actions"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crisis Actions',
            'res_model': 'risk.crisis.action',
            'view_mode': 'tree,form',
            'domain': [('crisis_id', '=', self.id)],
            'context': {'default_crisis_id': self.id},
        }

    def action_view_communications(self):
        """Ouvre la vue des communications"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Communications',
            'res_model': 'risk.crisis.communication',
            'view_mode': 'tree,form',
            'domain': [('crisis_id', '=', self.id)],
            'context': {'default_crisis_id': self.id},
        }

    def action_view_logs(self):
        """Ouvre la vue des logs"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crisis Logs',
            'res_model': 'risk.crisis.log',
            'view_mode': 'tree,form',
            'domain': [('crisis_id', '=', self.id)],
            'context': {'default_crisis_id': self.id},
        }

    # =====================================================
    # MÉTHODES DE CALCUL
    # =====================================================

    @api.depends('team_ids', 'action_ids', 'communication_ids', 'decision_ids', 'log_ids', 'rex_id')
    def _compute_statistics(self):
        for rec in self:
            rec.team_count = len(rec.team_ids)
            rec.action_count = len(rec.action_ids)
            rec.communication_count = len(rec.communication_ids)
            rec.decision_count = len(rec.decision_ids)
            rec.log_count = len(rec.log_ids)
            rec.rex_count = len(rec.rex_id)

    @api.depends('crisis_committee_meeting_ids')
    def _compute_meeting_count(self):
        for rec in self:
            rec.meeting_count = len(rec.crisis_committee_meeting_ids)

    # =====================================================
    # CRÉATION
    # =====================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('risk.crisis')
        return super().create(vals_list)