from dateutil.relativedelta import relativedelta
from odoo import models, fields, api


class RiskPolicy(models.Model):
    _name = 'risk.policy'
    _description = 'Document de Gouvernance (Politiques & Procédures)'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Indispensable pour le workflow d'approbation
    _rec_name = 'name'

    # Informations générales
    name = fields.Char(string='Titre du document', required=True, tracking=True)
    code = fields.Char(string='Référence', readonly=True, default='Nouveau', copy=False)
    document_type = fields.Selection([
        ('policy', 'Politique'),
        ('procedure', 'Procédure'),
        ('standard', 'Standard / Norme'),
        ('charter', 'Charte'),
        ('guideline', 'Ligne directrice')
    ], string='Type de document', required=True, tracking=True)

    version = fields.Char(string='Version', default='1.0', tracking=True)

    # Contenu
    description = fields.Text(string='Objectif / Résumé')
    content = fields.Html(string='Contenu du document')
    attachment_ids = fields.Many2many('ir.attachment', string='Fichiers joints')

    # Responsabilités
    owner_id = fields.Many2one('res.users', string='Propriétaire (Owner)', required=True, tracking=True,
                               help="Personne responsable de la mise à jour du document.")
    approver_id = fields.Many2one('res.users', string='Approbateur', tracking=True)
    department_ids = fields.Many2many('hr.department', string='Départements concernés')

    # Cycle de vie et Workflow
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('review', 'En revue'),
        ('approved', 'Approuvé'),
        ('published', 'Publié / En vigueur'),
        ('archived', 'Obsolète / Archivé')
    ], string='Statut', default='draft', tracking=True)

    # Dates et Révisions
    effective_date = fields.Date(string="Date d'entrée en vigueur", tracking=True)
    review_frequency = fields.Selection([
        ('12', 'Annuelle'),
        ('24', 'Bisanuelle'),
        ('36', 'Tous les 3 ans')
    ], string='Fréquence de révision', default='12')
    next_review_date = fields.Date(string='Prochaine révision', compute='_compute_next_review_date', store=True)

    # Liens GRC (Très important pour faire le pont avec le reste du module)
    risk_ids = fields.Many2many('risk.risk', string='Risques couverts',
                                help="Risques que cette politique aide à mitiger.")
    control_ids = fields.Many2many('risk.control', string='Contrôles associés')
    regulation_ids = fields.Many2many('risk.regulation', string='Réglementations liées (Conformité)')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'Nouveau') == 'Nouveau':
                # N'oubliez pas de créer la séquence 'risk.policy.seq' en XML
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.policy.seq') or 'Nouveau'
        return super().create(vals_list)

    @api.depends('effective_date', 'review_frequency')
    def _compute_next_review_date(self):
        for record in self:
            if record.effective_date and record.review_frequency:
                record.next_review_date = record.effective_date + relativedelta(months=int(record.review_frequency))
            else:
                record.next_review_date = False

    # Actions du workflow
    def action_submit_review(self):
        self.state = 'review'
        # Logique optionnelle: Créer une activité (To-Do) pour l'approbateur

    def action_approve(self):
        self.state = 'approved'

    def action_publish(self):
        self.state = 'published'
        if not self.effective_date:
            self.effective_date = fields.Date.today()

    def action_archive(self):
        self.state = 'archived'