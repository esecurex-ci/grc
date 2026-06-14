from odoo import models, fields, api
from datetime import timedelta


class RiskCrisisCommandCenter(models.Model):
    _name = 'risk.crisis.command.center'
    _description = 'Crisis Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    # =====================================================
    # CHAMPS EXISTANTS (à garder)
    # =====================================================
    name = fields.Char(string='Crisis Name', required=True)
    description = fields.Html(string='Description')

    crisis_level = fields.Selection([
        ('1', 'Level 1 - Minor'),
        ('2', 'Level 2 - Moderate'),
        ('3', 'Level 3 - Major'),
        ('4', 'Level 4 - Critical')
    ], string='Crisis Level', default='1')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], default='draft')

    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    resolution_date = fields.Datetime(string='Resolution Date')

    # =====================================================
    # NOUVEAUX CHAMPS MTTR
    # =====================================================

    mttr_hours = fields.Float(
        compute='_compute_mttr_hours',
        string='MTTR (Hours)',
        help='Mean Time To Recovery - Temps moyen de récupération'
    )

    mttr_display = fields.Char(
        compute='_compute_mttr_display',
        string='MTTR',
        help='MTTR au format lisible (jours/heures)'
    )

    # =====================================================
    # CHAMPS WARROOM
    # =====================================================

    warroom_ids = fields.One2many(
        'risk.crisis.warroom',
        'crisis_id',
        string='War Rooms'
    )

    active_warroom_count = fields.Integer(
        compute='_compute_active_warroom_count',
        string='Active War Rooms',
        help='Nombre de salles de crise actives'
    )

    # =====================================================
    # CHAMPS ACTIONS ET DÉCISIONS
    # =====================================================

    action_ids = fields.One2many(
        'risk.crisis.action',
        'crisis_id',
        string='Actions'
    )

    action_count = fields.Integer(
        compute='_compute_action_count',
        string='Actions Count'
    )

    overdue_action_count = fields.Integer(
        compute='_compute_overdue_action_count',
        string='Overdue Actions',
        help='Actions en retard'
    )

    decision_ids = fields.One2many(
        'risk.crisis.committee.decision',
        'crisis_id',
        string='Decisions'
    )

    overdue_decision_count = fields.Integer(
        compute='_compute_overdue_decision_count',
        string='Overdue Decisions',
        help='Décisions en retard'
    )

    # =====================================================
    # CHAMPS REGULATOR
    # =====================================================

    regulator_reporting_ids = fields.One2many(
        'risk.crisis.regulatory.reporting',
        'crisis_id',
        string='Regulatory Reports'
    )

    regulator_reporting_count = fields.Integer(
        compute='_compute_regulator_reporting_count',
        string='Regulatory Reports',
        help='Nombre de rapports réglementaires'
    )

    regulator_communication_ids = fields.One2many(
        'risk.crisis.regulatory.communication',
        'crisis_id',
        string='Regulatory Communications'
    )

    regulator_communication_count = fields.Integer(
        compute='_compute_regulator_communication_count',
        string='Regulatory Communications',
        help='Nombre de communications réglementaires'
    )

    # =====================================================
    # CHAMPS DE COMPTAGE STANDARD
    # =====================================================

    meeting_ids = fields.One2many(
        'risk.crisis.committee.meeting',
        'crisis_id',
        string='Committee Meetings'
    )

    meeting_count = fields.Integer(
        compute='_compute_meeting_count',
        string='Meetings Count'
    )

    open_crisis_count = fields.Integer(
        compute='_compute_open_crisis_count',
        string='Open Crises'
    )

    # =====================================================
    # MÉTHODES DE CALCUL MTTR
    # =====================================================

    @api.depends('start_date', 'resolution_date', 'state')
    def _compute_mttr_hours(self):
        """Calcule le MTTR en heures (Mean Time To Recovery)"""
        for record in self:
            if record.state == 'resolved' and record.start_date and record.resolution_date:
                # Calcul en heures
                delta = record.resolution_date - record.start_date
                record.mttr_hours = delta.total_seconds() / 3600
            elif record.state == 'closed' and record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.mttr_hours = delta.total_seconds() / 3600
            else:
                record.mttr_hours = 0.0

    @api.depends('mttr_hours')
    def _compute_mttr_display(self):
        """Affiche le MTTR au format lisible"""
        for record in self:
            hours = record.mttr_hours
            if hours >= 24:
                days = int(hours // 24)
                remaining_hours = int(hours % 24)
                record.mttr_display = f"{days}j {remaining_hours}h"
            else:
                record.mttr_display = f"{int(hours)}h"

    # =====================================================
    # MÉTHODES WARROOM
    # =====================================================

    @api.depends('warroom_ids', 'warroom_ids.state')
    def _compute_active_warroom_count(self):
        """Compte les salles de crise actives"""
        for record in self:
            record.active_warroom_count = len(
                record.warroom_ids.filtered(lambda w: w.state == 'active')
            )

    # =====================================================
    # MÉTHODES ACTIONS ET DÉCISIONS
    # =====================================================

    @api.depends('action_ids')
    def _compute_action_count(self):
        for record in self:
            record.action_count = len(record.action_ids)

    @api.depends('action_ids', 'action_ids.deadline', 'action_ids.state')
    def _compute_overdue_action_count(self):
        """Compte les actions en retard non terminées"""
        for record in self:
            today = fields.Date.today()
            overdue = record.action_ids.filtered(
                lambda a: a.deadline and a.deadline < today and a.state not in ['done', 'cancelled']
            )
            record.overdue_action_count = len(overdue)

    @api.depends('decision_ids', 'decision_ids.deadline')
    def _compute_overdue_decision_count(self):
        """Compte les décisions en retard"""
        for record in self:
            today = fields.Date.today()
            overdue = record.decision_ids.filtered(
                lambda d: d.deadline and d.deadline < today and d.state != 'implemented'
            )
            record.overdue_decision_count = len(overdue)

    # =====================================================
    # MÉTHODES REGULATOR
    # =====================================================

    @api.depends('regulator_reporting_ids')
    def _compute_regulator_reporting_count(self):
        for record in self:
            record.regulator_reporting_count = len(record.regulator_reporting_ids)

    @api.depends('regulator_communication_ids')
    def _compute_regulator_communication_count(self):
        for record in self:
            record.regulator_communication_count = len(record.regulator_communication_ids)

    # =====================================================
    # MÉTHODES STANDARD
    # =====================================================

    @api.depends('meeting_ids')
    def _compute_meeting_count(self):
        for record in self:
            record.meeting_count = len(record.meeting_ids)

    @api.depends('state')
    def _compute_open_crisis_count(self):
        """Calcule le nombre de crises ouvertes"""
        for record in self:
            record.open_crisis_count = self.search_count([
                ('state', 'in', ['draft', 'active'])
            ])

    # =====================================================
    # MÉTHODES D'ACTION
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

    def action_view_warrooms(self):
        """Ouvre la vue des salles de crise"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'War Rooms',
            'res_model': 'risk.crisis.warroom',
            'view_mode': 'tree,form',
            'domain': [('crisis_id', '=', self.id)],
            'context': {'default_crisis_id': self.id},
        }

    def action_view_overdue_actions(self):
        """Ouvre la vue des actions en retard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Overdue Actions',
            'res_model': 'risk.crisis.action',
            'view_mode': 'tree,form',
            'domain': [('crisis_id', '=', self.id), ('deadline', '<', fields.Date.today()),
                       ('state', 'not in', ['done', 'cancelled'])],
        }

    def action_view_regulator_reports(self):
        """Ouvre la vue des rapports réglementaires"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Regulatory Reports',
            'res_model': 'risk.crisis.regulatory.reporting',
            'view_mode': 'tree,form',
            'domain': [('crisis_id', '=', self.id)],
            'context': {'default_crisis_id': self.id},
        }

    def action_resolve(self):
        """Résoudre la crise"""
        self.ensure_one()
        self.state = 'resolved'
        if not self.resolution_date:
            self.resolution_date = fields.Datetime.now()

    def action_close(self):
        """Fermer la crise"""
        self.ensure_one()
        self.state = 'closed'
        if not self.end_date:
            self.end_date = fields.Datetime.now()