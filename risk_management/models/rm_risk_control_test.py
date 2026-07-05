from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RiskControlTest(models.Model):
    _name = 'risk.control.test'
    _description = 'Test de contrôle'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'test_date desc, id desc'

    # ============================================================
    # INFORMATIONS GÉNÉRALES
    # ============================================================

    name = fields.Char(
        string='Nom du test',
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

    control_id = fields.Many2one(
        'risk.control',
        string='Contrôle',
        required=True,
        ondelete='cascade',
        tracking=True
    )

    # ============================================================
    # DÉROULEMENT
    # ============================================================

    test_date = fields.Date(
        string='Date du test',
        required=True,
        default=fields.Date.today,
        tracking=True
    )

    tester_id = fields.Many2one(
        'hr.employee',
        string='Testeur',
        required=True,
        tracking=True
    )

    test_method = fields.Text(
        string='Méthode de test',
        help="Description de la méthode utilisée pour le test"
    )

    sample_size = fields.Integer(
        string='Taille de l\'échantillon',
        default=10,
        help="Nombre d'éléments testés"
    )

    # ============================================================
    # RÉSULTATS
    # ============================================================

    result = fields.Selection([
        ('pass', '✅ Réussi'),
        ('fail', '❌ Échec'),
        ('partial', '⚠️ Partiel'),
        ('not_applicable', '⚪ Non applicable'),
    ], string='Résultat', required=True, default='not_applicable', tracking=True)

    # ✅ Score du résultat (pour calculs)
    result_score = fields.Float(
        compute='_compute_result_score',
        string='Score du résultat',
        help="Score numérique du résultat (100 = Réussi, 50 = Partiel, 0 = Échec)"
    )

    # ✅ Nombre d'erreurs
    error_count = fields.Integer(
        string='Nombre d\'erreurs',
        default=0,
        help="Nombre d'erreurs détectées lors du test"
    )

    # ✅ Taux d'erreur
    error_rate = fields.Float(
        compute='_compute_error_rate',
        string='Taux d\'erreur (%)',
        help="(Nombre d'erreurs / Taille de l'échantillon) × 100"
    )

    # ✅ Taux de conformité
    compliance_rate = fields.Float(
        compute='_compute_compliance_rate',
        string='Taux de conformité (%)',
        help="(Éléments conformes / Taille de l'échantillon) × 100"
    )

    details = fields.Html(
        string='Détails du test',
        help="Détails des résultats du test"
    )

    deviation = fields.Html(
        string='Écarts constatés',
        help="Description des écarts constatés"
    )

    recommendation = fields.Html(
        string='Recommandations',
        help="Recommandations suite au test"
    )

    # ============================================================
    # ACTIONS CORRECTIVES
    # ============================================================

    action_ids = fields.Many2many(
        'risk.corrective.action',
        'risk_test_action_rel',
        'test_id',
        'action_id',
        string='Actions correctives'
    )

    corrective_action_taken = fields.Boolean(
        string='Action corrective prise',
        default=False
    )

    corrective_action_date = fields.Date(
        string='Date de l\'action corrective'
    )

    # ============================================================
    # DOCUMENTS
    # ============================================================

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Pièces jointes'
    )

    # ============================================================
    # STATUT
    # ============================================================

    state = fields.Selection([
        ('draft', '📝 Brouillon'),
        ('planned', '📅 Planifié'),
        ('in_progress', '🔄 En cours'),
        ('done', '✅ Terminé'),
        ('cancelled', '❌ Annulé'),
    ], string='Statut', default='draft', tracking=True)

    # ============================================================
    # COMPUTES
    # ============================================================

    @api.depends('result')
    def _compute_result_score(self):
        scores = {
            'pass': 100,
            'partial': 50,
            'fail': 0,
            'not_applicable': 0,
        }
        for record in self:
            record.result_score = scores.get(record.result, 0)

    @api.depends('error_count', 'sample_size')
    def _compute_error_rate(self):
        for record in self:
            if record.sample_size and record.sample_size > 0:
                record.error_rate = (record.error_count / record.sample_size) * 100
            else:
                record.error_rate = 0

    @api.depends('error_count', 'sample_size')
    def _compute_compliance_rate(self):
        for record in self:
            if record.sample_size and record.sample_size > 0:
                compliant = record.sample_size - record.error_count
                record.compliance_rate = (compliant / record.sample_size) * 100
            else:
                record.compliance_rate = 100

    # ============================================================
    # CONTRAINTES
    # ============================================================

    @api.constrains('error_count', 'sample_size')
    def _check_error_count(self):
        for record in self:
            if record.error_count > record.sample_size:
                raise ValidationError(_("Le nombre d'erreurs ne peut pas dépasser la taille de l'échantillon."))

    # ============================================================
    # MÉTHODES D'ACTION
    # ============================================================

    def action_pass(self):
        """Marque le test comme réussi"""
        self.ensure_one()
        self.result = 'pass'
        self.state = 'done'
        return True

    def action_fail(self):
        """Marque le test comme échec"""
        self.ensure_one()
        self.result = 'fail'
        self.state = 'done'
        return True

    def action_partial(self):
        """Marque le test comme partiel"""
        self.ensure_one()
        self.result = 'partial'
        self.state = 'done'
        return True

    def action_plan(self):
        """Planifie le test"""
        self.ensure_one()
        self.state = 'planned'
        return True

    def action_start(self):
        """Démarre le test"""
        self.ensure_one()
        self.state = 'in_progress'
        return True

    def action_create_corrective_action(self):
        """Crée une action corrective pour ce test"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créer une action corrective',
            'res_model': 'risk.corrective.action',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': f'Action suite au test {self.code or self.name}',
                'default_description': f'Action suite au test du {self.test_date}',
                'default_control_test_id': self.id,
                'default_control_id': self.control_id.id,
            },
        }

    def action_cancel(self):
        """Annule le test"""
        self.ensure_one()
        self.state = 'cancelled'
        return True

    def action_reset_to_draft(self):
        """Remet le test en brouillon"""
        self.ensure_one()
        self.state = 'draft'
        return True