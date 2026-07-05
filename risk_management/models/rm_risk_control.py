from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskControl(models.Model):
    _name = 'risk.control'
    _description = 'Contrôle interne'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code, name'

    # ============================================================
    # INFORMATIONS GÉNÉRALES
    # ============================================================

    name = fields.Char(
        string='Nom du contrôle',
        required=True,
        tracking=True
    )

    code = fields.Char(
        string='Code',
        tracking=True
    )

    description = fields.Html(
        string='Description'
    )

    # ============================================================
    # CLASSIFICATION
    # ============================================================

    control_type = fields.Selection([
        ('preventive', '🛡️ Préventif'),
        ('detective', '🔍 Détectif'),
        ('corrective', '🔧 Correctif'),
        ('directive', '📋 Directif'),
    ], string='Type de contrôle', default='preventive', required=True, tracking=True)

    control_nature = fields.Selection([
        ('manual', '✋ Manuel'),
        ('automatic', '🤖 Automatique'),
        ('semi_automatic', '⚡ Semi-automatique'),
    ], string='Nature du contrôle', default='manual', tracking=True)

    # ✅ CORRIGÉ : frequency → control_frequency
    control_frequency = fields.Selection([
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
        ('quarterly', 'Trimestriel'),
        ('annual', 'Annuel'),
        ('on_demand', 'À la demande'),
    ], string='Fréquence', default='monthly', tracking=True)

    # ✅ ALIAS pour compatibilité
    frequency = fields.Selection(
        related='control_frequency',
        string='Fréquence',
        store=True
    )

    # ============================================================
    # CONTEXTE
    # ============================================================

    process_id = fields.Many2one(
        'risk.process',
        string='Processus',
        tracking=True
    )

    activity_id = fields.Many2one(
        'risk.activity',
        string='Activité',
        tracking=True
    )

    risk_ids = fields.Many2many(
        'risk.risk',
        string='Risques couverts'
    )

    # ============================================================
    # RESPONSABLES
    # ============================================================

    owner_id = fields.Many2one(
        'hr.employee',
        string='Propriétaire du contrôle',
        tracking=True
    )

    reviewer_id = fields.Many2one(
        'hr.employee',
        string='Relecteur',
        tracking=True
    )

    tester_id = fields.Many2one(
        'hr.employee',
        string='Testeur',
        tracking=True
    )

    # ============================================================
    # EFFICACITÉ
    # ============================================================

    # ✅ CORRIGÉ : effectiveness_level → effectiveness
    effectiveness = fields.Selection([
        ('high', '🟢 Élevée'),
        ('medium', '🟡 Moyenne'),
        ('low', '🔴 Faible'),
        ('not_tested', '⚪ Non testé'),
    ], string='Efficacité', default='not_tested', tracking=True)

    # ✅ ALIAS pour compatibilité
    effectiveness_level = fields.Selection(
        related='effectiveness',
        string='Niveau d\'efficacité',
        store=True
    )

    effectiveness_score = fields.Float(
        compute='_compute_effectiveness_score',
        string='Score d\'efficacité (%)'
    )

    # ============================================================
    # TESTS DE CONTRÔLE
    # ============================================================

    test_ids = fields.One2many(
        'risk.control.test',
        'control_id',
        string='Tests'
    )

    last_test_date = fields.Date(
        compute='_compute_last_test',
        string='Dernier test'
    )

    test_count = fields.Integer(
        compute='_compute_test_count',
        string="Nombre de tests"
    )

    test_success_rate = fields.Float(
        compute='_compute_test_stats',
        string="Taux de réussite (%)"
    )

    # ============================================================
    # DOCUMENTS
    # ============================================================

    procedure_id = fields.Many2one(
        'risk.document',
        string='Procédure associée'
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Documents joints'
    )

    # ============================================================
    # STATUT
    # ============================================================

    state = fields.Selection([
        ('draft', '📝 Brouillon'),
        ('active', '✅ Actif'),
        ('review', '🔍 En revue'),
        ('obsolete', '📦 Obsolète'),
    ], string='Statut', default='draft', tracking=True)

    active = fields.Boolean(
        default=True,
        string='Actif'
    )

    automation_level = fields.Selection(
        related='control_nature',
        string='Niveau d\'automatisation',
        store=True
    )

    # ============================================================
    # COMPUTES
    # ============================================================

    @api.depends('test_ids.test_date')
    def _compute_last_test(self):
        for record in self:
            latest = record.test_ids.sorted('test_date', reverse=True)[:1]
            record.last_test_date = latest.test_date if latest else False

    @api.depends('test_ids')
    def _compute_test_count(self):
        for record in self:
            record.test_count = len(record.test_ids)

    @ api.depends('test_ids', 'test_ids.result')
    def _compute_test_stats(self):
        for record in self:
            if record.test_count > 0:
                success = len(record.test_ids.filtered(lambda t: t.result == 'pass'))
                record.test_success_rate = (success / record.test_count) * 100
            else:
                record.test_success_rate = 0

    @api.depends('effectiveness')
    def _compute_effectiveness_score(self):
        scores = {
            'high': 90,
            'medium': 60,
            'low': 30,
            'not_tested': 0,
        }
        for record in self:
            record.effectiveness_score = scores.get(record.effectiveness, 0)

    # ============================================================
    # MÉTHODES D'ACTION
    # ============================================================

    def action_activate(self):
        """Active le contrôle"""
        self.ensure_one()
        self.state = 'active'
        return True

    def action_review(self):
        """Met le contrôle en revue"""
        self.ensure_one()
        self.state = 'review'
        return True

    def action_obsolete(self):
        """Rend le contrôle obsolète"""
        self.ensure_one()
        self.state = 'obsolete'
        self.active = False
        return True

    def action_add_test(self):
        """Crée un nouveau test"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ajouter un test - {self.name}',
            'res_model': 'risk.control.test',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_control_id': self.id,
                'default_test_date': fields.Date.today(),
            },
        }

    def action_view_tests(self):
        """Voir tous les tests"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Tests - {self.name}',
            'res_model': 'risk.control.test',
            'view_mode': 'list,form',
            'domain': [('control_id', '=', self.id)],
        }

    def action_generate_report(self):
        """Génère un rapport sur le contrôle"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Rapport - {self.name}',
            'res_model': 'risk.control.report',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_control_id': self.id},
        }

    # ============================================================
    # CONTRAINTES
    # ============================================================

    @api.constrains('code')
    def _check_code(self):
        for record in self:
            if record.code and self.search([('code', '=', record.code), ('id', '!=', record.id)]):
                raise ValidationError(_("Le code '%s' est déjà utilisé.") % record.code)