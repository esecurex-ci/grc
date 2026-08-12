from datetime import timedelta

from odoo import models, fields, api


class RiskBia(models.Model):
    _name = 'risk.bia'
    _description = 'Business Impact Analysis'
    _inherit = ['mail.thread',]  # Enlever 'mail.activity.mixin'

    name = fields.Char(required=True)
    description = fields.Html()
    process_id = fields.Many2one('risk.process', required=True)
    owner_id = fields.Many2one('hr.employee')
    assessment_date = fields.Date()

    # CORRECTION : Utiliser 'approved' au lieu de 'validated'
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),  # Changé de 'validated' à 'approved'
        ('archived', 'Archived')  # Ajouté pour action_archive
    ], default='draft')

    activity_ids = fields.One2many('risk.bia.activity', 'bia_id', string='Activities')
    activity_count = fields.Integer(compute='_compute_activity_count')
    mtd = fields.Integer(string='MTD (heures)', help='Maximum Tolerable Downtime')
    rto = fields.Integer(string='RTO (heures)', help='Recovery Time Objective')
    rpo = fields.Integer(string='RPO (heures)', help='Recovery Point Objective')
    priority = fields.Selection(
        [
            ('1', 'Very Low'),
            ('2', 'Low'),
            ('3', 'Medium'),
            ('4', 'High'),
            ('5', 'Critical')
        ],
        string='Priority',
        compute='_compute_priority',
        store=True
    )

    impact_operational = fields.Selection(
        [
            ('1', 'Très faible'),
            ('2', 'Faible'),
            ('3', 'Moyen'),
            ('4', 'Élevé'),
            ('5', 'Critique')
        ],
        string='Impact Opérationnel',
        required=True,
        default='1',
        help='Impact sur les opérations quotidiennes'
    )

    impact_financial = fields.Selection(
        [
            ('1', 'Très faible'),
            ('2', 'Faible'),
            ('3', 'Moyen'),
            ('4', 'Élevé'),
            ('5', 'Critique')
        ],
        string='Impact Financier',
        required=True,
        default='1',
        help='Impact financier estimé'
    )

    # ------------------------------------------------------------------
    # ✅ Alignement ISO/TS 22317 (BIA) — champs ajoutés, aucun champ
    # existant retiré ni renommé, pour ne pas casser les BIA déjà saisies.
    # ------------------------------------------------------------------

    mbco = fields.Html(
        string='Niveau de service minimal (MBCO)',
        help="Minimum Business Continuity Objective : le niveau de service "
             "minimal acceptable pendant la période de reprise, distinct du "
             "RTO (délai) — notion attendue par ISO/TS 22317."
    )

    peak_period_notes = fields.Html(
        string='Périodes de pointe / saisonnalité',
        help="ISO/TS 22317 recommande de documenter les variations "
             "d'impact selon la période (ex. clôture mensuelle, fin "
             "d'exercice) plutôt qu'un impact unique et constant dans le "
             "temps."
    )

    next_review_date = fields.Date(
        string='Prochaine révision',
        help="Une BIA approuvée doit être revue périodiquement (ISO 22301) "
             "— ce champ permet de détecter les BIA à revoir."
    )

    risk_ids = fields.Many2many(
        'risk.risk',
        string='Risques associés',
        help="Traçabilité vers le registre des risques : une BIA identifie "
             "des expositions (perte de processus critique) qui devraient "
             "normalement correspondre à des risques déjà répertoriés."
    )

    approved_date = fields.Date(
        string='Date d\'approbation',
        readonly=True
    )

    approved_by = fields.Many2one(
        'res.users',
        string='Approuvé par',
        readonly=True
    )

    def action_approve(self):
        """Approuver l'analyse BIA.

        Renseigne également la date/l'auteur d'approbation et, si absente,
        une prochaine date de révision à horizon 1 an (revue périodique
        attendue par ISO 22301) — sans jamais écraser une valeur déjà
        saisie manuellement."""
        for record in self:
            record.state = 'approved'
            record.approved_date = fields.Date.today()
            record.approved_by = self.env.user
            if not record.next_review_date:
                record.next_review_date = fields.Date.today() + timedelta(days=365)
        return True

    def action_draft(self):
        """Remettre en brouillon"""
        for record in self:
            record.state = 'draft'
        return True

    def action_archive(self):
        """Archiver l'analyse"""
        for record in self:
            record.state = 'archived'
        return True

    @api.depends('activity_ids')
    def _compute_activity_count(self):
        for rec in self:
            rec.activity_count = len(rec.activity_ids)

    # ------------------------------------------------------------------
    # ✅ "Pourquoi on ne voit pas le PCA depuis une BIA ?" — risk.bcp.plan.
    # bia_id référence la BIA depuis le PCA, mais la BIA elle-même ne
    # montrait cette relation nulle part. Vue en lecture (le lien se crée
    # côté PCA, via bia_id), sur le même principe que le bouton Activités.
    # ------------------------------------------------------------------

    bcp_plan_ids = fields.One2many(
        'risk.bcp.plan',
        'bia_id',
        string='PCA associés'
    )

    bcp_plan_count = fields.Integer(
        compute='_compute_bcp_plan_count'
    )

    @api.depends('bcp_plan_ids')
    def _compute_bcp_plan_count(self):
        for rec in self:
            rec.bcp_plan_count = len(rec.bcp_plan_ids)

    def action_view_bcp_plans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'PCA associés',
            'res_model': 'risk.bcp.plan',
            'view_mode': 'list,form',
            'domain': [('bia_id', '=', self.id)],
            'context': {'default_bia_id': self.id}
        }

    def action_view_activities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Critical Activities',
            'res_model': 'risk.bia.activity',
            'view_mode': 'list,form',
            'domain': [('bia_id', '=', self.id)],
            'context': {'default_bia_id': self.id}
        }

    @api.depends('impact_operational', 'impact_financial')
    def _compute_priority(self):
        for rec in self:
            op = int(rec.impact_operational or 1)
            fin = int(rec.impact_financial or 1)
            max_impact = max(op, fin)
            rec.priority = str(max_impact)

