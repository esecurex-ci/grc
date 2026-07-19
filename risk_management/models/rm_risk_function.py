# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class RiskFunction(models.Model):
    _name = 'risk.function'
    _description = 'Fonction organisationnelle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'

    name = fields.Char(string='Nom de la fonction', required=True, tracking=True)
    code = fields.Char(string='Code', readonly=True, default='New', tracking=True)
    description = fields.Html(string='Description', tracking=True)

    # Hiérarchie
    parent_id = fields.Many2one('risk.function', string='Fonction parente', tracking=True, index=True)
    child_ids = fields.One2many('risk.function', 'parent_id', string='Sous-fonctions')
    parent_path = fields.Char(index=True, recursive=True)

    # Responsables
    manager_id = fields.Many2one('hr.employee', string='Responsable de la fonction', tracking=True)
    deputy_manager_id = fields.Many2one('hr.employee', string='Responsable adjoint', tracking=True)

    # Informations
    company_id = fields.Many2one('res.company', string='Société', default=lambda self: self.env.company)
    department_id = fields.Many2one('hr.department', string='Département', tracking=True)

    # Risques associés
    risk_ids = fields.Many2many('risk.risk', string='Risques associés')
    risk_count = fields.Integer(
        compute='_compute_risk_count',
        string="Nombre de risques",
        store=True,
        index=True
    )

    # Contrôles associés
    control_ids = fields.Many2many('risk.control', string='Contrôles associés')
    control_count = fields.Integer(
        compute='_compute_control_count',
        string="Nombre de contrôles",
        store=True,
        index=True
    )

    # KRI associés
    kri_ids = fields.Many2many('risk.kri', string='KRI associés')
    kri_count = fields.Integer(
        compute='_compute_kri_count',
        string="Nombre de KRI",
        store=True,
        index=True
    )

    # Incidents
    incident_ids = fields.Many2many('risk.incident', string='Incidents associés')
    incident_count = fields.Integer(
        compute='_compute_incident_count',
        string="Nombre d'incidents",
        store=True,
        index=True
    )

    # Statistiques
    total_risk_score = fields.Integer(compute='_compute_stats', string='Score total des risques')
    avg_risk_score = fields.Float(compute='_compute_stats', string='Score moyen des risques')
    critical_risk_count = fields.Integer(compute='_compute_stats', string='Risques critiques')
    high_risk_count = fields.Integer(compute='_compute_stats', string='Risques élevés')
    medium_risk_count = fields.Integer(compute='_compute_stats', string='Risques moyens')
    low_risk_count = fields.Integer(compute='_compute_stats', string='Risques faibles')

    # État
    active = fields.Boolean(string='Actif', default=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('archived', 'Archivé'),
    ], string='Statut', default='draft', tracking=True)

    # Dates
    creation_date = fields.Date(string='Date de création', default=fields.Date.today)
    last_review_date = fields.Date(string='Date de dernière révision', tracking=True)
    next_review_date = fields.Date(compute='_compute_next_review_date', store=True, string='Prochaine révision')

    # Review frequency
    review_frequency = fields.Selection([
        ('monthly', 'Mensuelle'),
        ('quarterly', 'Trimestrielle'),
        ('semiannual', 'Semestrielle'),
        ('annual', 'Annuelle'),
    ], string='Fréquence de révision', default='quarterly', tracking=True)

    # Documents
    document_ids = fields.Many2many('risk.document', string='Documents')
    document_count = fields.Integer(
        compute='_compute_document_count',
        string="Nombre de documents",
        store=True,
        index=True
    )

    # ✅ Correction : Ajouter recursive=True pour les champs hiérarchiques
    complete_name = fields.Char(
        compute='_compute_complete_name',
        string='Nom complet',
        store=True,
        recursive=True  # ✅ Important pour les champs hiérarchiques
    )

    level = fields.Integer(
        compute='_compute_level',
        string='Niveau hiérarchique',
        store=True,
        recursive=True  # ✅ Important pour les champs hiérarchiques
    )

    # ============================================================
    # COMPUTE METHODS
    # ============================================================

    @api.depends('risk_ids')
    def _compute_risk_count(self):
        for record in self:
            record.risk_count = len(record.risk_ids)

    @api.depends('control_ids')
    def _compute_control_count(self):
        for record in self:
            record.control_count = len(record.control_ids)

    @api.depends('kri_ids')
    def _compute_kri_count(self):
        for record in self:
            record.kri_count = len(record.kri_ids)

    @api.depends('incident_ids')
    def _compute_incident_count(self):
        for record in self:
            record.incident_count = len(record.incident_ids)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends('risk_ids', 'risk_ids.inherent_score')
    def _compute_stats(self):
        for record in self:
            risks = record.risk_ids
            record.total_risk_score = sum(risks.mapped('inherent_score') or [0])
            record.avg_risk_score = round(record.total_risk_score / len(risks), 1) if risks else 0
            record.critical_risk_count = len(risks.filtered(lambda r: r.inherent_level == 'critical'))
            record.high_risk_count = len(risks.filtered(lambda r: r.inherent_level == 'high'))
            record.medium_risk_count = len(risks.filtered(lambda r: r.inherent_level == 'medium'))
            record.low_risk_count = len(risks.filtered(lambda r: r.inherent_level == 'low'))

    @api.depends('parent_id', 'parent_id.complete_name', 'name')
    def _compute_complete_name(self):
        for record in self:
            if record.parent_id:
                record.complete_name = f"{record.parent_id.complete_name} / {record.name}"
            else:
                record.complete_name = record.name

    @api.depends('parent_id', 'parent_id.level')
    def _compute_level(self):
        for record in self:
            if record.parent_id:
                record.level = record.parent_id.level + 1
            else:
                record.level = 0

    @api.depends('last_review_date', 'review_frequency')
    def _compute_next_review_date(self):
        for record in self:
            if not record.last_review_date:
                record.next_review_date = False
                continue

            if record.review_frequency == 'monthly':
                record.next_review_date = record.last_review_date + relativedelta(months=1)
            elif record.review_frequency == 'quarterly':
                record.next_review_date = record.last_review_date + relativedelta(months=3)
            elif record.review_frequency == 'semiannual':
                record.next_review_date = record.last_review_date + relativedelta(months=6)
            elif record.review_frequency == 'annual':
                record.next_review_date = record.last_review_date + relativedelta(years=1)

    # ============================================================
    # CONSTRAINTS
    # ============================================================

    @api.constrains('parent_id')
    def _check_parent_id(self):
        for record in self:
            if record.parent_id:
                if record.id == record.parent_id.id:
                    raise ValidationError("Une fonction ne peut pas être sa propre parente.")
                # Vérifier la récursivité
                parent = record.parent_id
                while parent:
                    if parent.id == record.id:
                        raise ValidationError("Une fonction ne peut pas avoir une relation circulaire.")
                    parent = parent.parent_id

    # ============================================================
    # CRUD METHODS
    # ============================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.function')
        return super().create(vals_list)

    def name_get(self):
        result = []
        for record in self:
            name = record.complete_name or record.name
            result.append((record.id, name))
        return result

    # ============================================================
    # ACTION METHODS
    # ============================================================

    def action_view_risks(self):
        """Voir les risques associés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Risques - {self.name}',
            'res_model': 'risk.risk',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', self.risk_ids.ids)],
            'context': {'default_function_id': self.id},
        }

    def action_view_controls(self):
        """Voir les contrôles associés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Contrôles - {self.name}',
            'res_model': 'risk.control',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.control_ids.ids)],
        }

    def action_view_kris(self):
        """Voir les KRI associés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'KRI - {self.name}',
            'res_model': 'risk.kri',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.kri_ids.ids)],
        }

    def action_view_incidents(self):
        """Voir les incidents associés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Incidents - {self.name}',
            'res_model': 'risk.incident',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.incident_ids.ids)],
        }

    def action_view_documents(self):
        """Voir les documents associés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Documents - {self.name}',
            'res_model': 'risk.document',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', self.document_ids.ids)],
        }

    def action_activate(self):
        """Activer la fonction"""
        self.write({'state': 'active', 'active': True})

    def action_archive(self):
        """Archiver la fonction"""
        self.write({'state': 'archived', 'active': False})

    def action_review(self):
        """Marquer comme révisé"""
        self.write({
            'last_review_date': fields.Date.today(),
            'state': 'active'
        })

    def action_get_children(self):
        """Récupérer toutes les sous-fonctions (récursif)"""
        children = self
        for child in self.child_ids:
            children |= child.action_get_children()
        return children

    def action_get_all_risks(self):
        """Récupérer tous les risques de la fonction et ses sous-fonctions"""
        functions = self.action_get_children()
        return self.env['risk.risk'].search([
            ('function_id', 'in', functions.ids)
        ])