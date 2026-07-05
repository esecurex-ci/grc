from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskDmr(models.Model):
    _name = 'risk.dmr'
    _description = 'Dispositif de Maîtrise des Risques'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'code, name'
    _rec_name = 'name'

    # ============================================================
    # INFORMATIONS GÉNÉRALES
    # ============================================================

    name = fields.Char(
        string='Nom du Dispositif',
        required=True,
        tracking=True
    )

    code = fields.Char(
        string='Code',
        required=True,
        tracking=True
    )

    description = fields.Html(
        string='Description'
    )

    # ============================================================
    # CONTEXTE
    # ============================================================

    function_id = fields.Many2one(
        'risk.function',
        string='Fonction concernée',
        tracking=True
    )

    process_id = fields.Many2one(
        'risk.process',
        string='Processus concerné',
        tracking=True
    )

    # ============================================================
    # COMPOSANTS DU DISPOSITIF
    # ============================================================

    # 1. Contrôles
    control_ids = fields.Many2many(
        'risk.control',
        'risk_dmr_control_rel',
        'dmr_id',
        'control_id',
        string='Contrôles'
    )

    # 2. Tests de contrôle
    test_ids = fields.Many2many(
        'risk.control.test',
        'risk_dmr_test_rel',
        'dmr_id',
        'test_id',
        string='Tests de contrôle'
    )

    # 3. Actions correctives
    action_ids = fields.Many2many(
        'risk.corrective.action',
        'risk_dmr_action_rel',
        'dmr_id',
        'action_id',
        string='Actions correctives'
    )

    # 4. KRI associés
    kri_ids = fields.Many2many(
        'risk.kri',
        'risk_dmr_kri_rel',
        'dmr_id',
        'kri_id',
        string='KRI associés'
    )

    # 5. Procédures
    procedure_ids = fields.Many2many(
        'risk.document',
        'risk_dmr_procedure_rel',
        'dmr_id',
        'procedure_id',
        string='Procédures associées'
    )

    # ============================================================
    # SYNTHÈSE
    # ============================================================

    # Statistiques des contrôles
    control_count = fields.Integer(
        compute='_compute_stats',
        string='Nombre de contrôles'
    )

    control_effective_count = fields.Integer(
        compute='_compute_stats',
        string='Contrôles efficaces'
    )

    control_ineffective_count = fields.Integer(
        compute='_compute_stats',
        string='Contrôles inefficaces'
    )

    # Statistiques des tests
    test_count = fields.Integer(
        compute='_compute_stats',
        string='Nombre de tests'
    )

    test_pass_count = fields.Integer(
        compute='_compute_stats',
        string='Tests réussis'
    )

    test_fail_count = fields.Integer(
        compute='_compute_stats',
        string='Tests échoués'
    )

    # Statistiques des actions
    action_count = fields.Integer(
        compute='_compute_stats',
        string='Nombre d\'actions'
    )

    action_done_count = fields.Integer(
        compute='_compute_stats',
        string='Actions terminées'
    )

    action_overdue_count = fields.Integer(
        compute='_compute_stats',
        string='Actions en retard'
    )

    # Taux de conformité global
    compliance_rate = fields.Float(
        compute='_compute_compliance_rate',
        string='Taux de conformité global (%)'
    )

    # ============================================================
    # RESPONSABLES
    # ============================================================

    owner_id = fields.Many2one(
        'hr.employee',
        string='Responsable du dispositif',
        required=True,
        tracking=True
    )

    approver_id = fields.Many2one(
        'hr.employee',
        string='Approbateur',
        tracking=True
    )

    # ============================================================
    # STATUT
    # ============================================================

    state = fields.Selection([
        ('draft', '📝 En construction'),
        ('active', '✅ Actif'),
        ('review', '🔍 En revue'),
        ('obsolete', '📦 Obsolète'),
    ], string='Statut', default='draft', tracking=True)

    active = fields.Boolean(default=True)

    # ============================================================
    # COMPUTES
    # ============================================================

    @api.depends(
        'control_ids', 'control_ids.effectiveness',
        'test_ids', 'test_ids.result',
        'action_ids', 'action_ids.state'
    )
    def _compute_stats(self):
        for record in self:
            # Contrôles
            record.control_count = len(record.control_ids)
            record.control_effective_count = len(
                record.control_ids.filtered(lambda c: c.effectiveness in ['high', 'medium'])
            )
            record.control_ineffective_count = len(
                record.control_ids.filtered(lambda c: c.effectiveness in ['low', 'not_tested'])
            )

            # Tests
            record.test_count = len(record.test_ids)
            record.test_pass_count = len(
                record.test_ids.filtered(lambda t: t.result == 'pass')
            )
            record.test_fail_count = len(
                record.test_ids.filtered(lambda t: t.result in ['fail', 'partial'])
            )

            # Actions
            record.action_count = len(record.action_ids)
            record.action_done_count = len(
                record.action_ids.filtered(lambda a: a.state == 'done')
            )
            record.action_overdue_count = len(
                record.action_ids.filtered(lambda a: a.state == 'overdue')
            )

    @api.depends('control_count', 'control_effective_count', 'test_count', 'test_pass_count')
    def _compute_compliance_rate(self):
        for record in self:
            total = record.control_count + record.test_count
            if total > 0:
                compliant = record.control_effective_count + record.test_pass_count
                record.compliance_rate = (compliant / total) * 100
            else:
                record.compliance_rate = 0

    # ============================================================
    # MÉTHODES D'ACTION
    # ============================================================

    def action_activate(self):
        """Active le dispositif"""
        self.ensure_one()
        self.state = 'active'
        return True

    def action_review(self):
        """Met en revue"""
        self.ensure_one()
        self.state = 'review'
        return True

    def action_obsolete(self):
        """Rend obsolète"""
        self.ensure_one()
        self.state = 'obsolete'
        self.active = False
        return True

    def action_view_controls(self):
        """Voir les contrôles"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Contrôles - {self.name}',
            'res_model': 'risk.control',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', self.control_ids.ids)],
        }

    def action_view_tests(self):
        """Voir les tests"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Tests - {self.name}',
            'res_model': 'risk.control.test',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.test_ids.ids)],
        }

    def action_view_actions(self):
        """Voir les actions"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Actions - {self.name}',
            'res_model': 'risk.corrective.action',
            'view_mode': 'list,form,kanban',
            'domain': [('id', 'in', self.action_ids.ids)],
        }