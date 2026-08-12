from datetime import timedelta

from odoo import models, fields, api


class RiskDrpPlan(models.Model):
    _name = 'risk.drp.plan'
    _description = 'Plan de récupération des données'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True,
        string="Nom du plan"
    )

    system_id = fields.Many2one(
        'risk.asset',
        string="Système"
    )

    recovery_site_id = fields.Many2one(
        'risk.recovery.site',
        string="Site de récupération"
    )

    recovery_procedure = fields.Html(string="Procédure de récupération")

    backup_strategy = fields.Html(string="Stratégie de sauvegarde")

    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('approved', 'Approuvé')
        ],
        default='draft',
        string='Statut'
    )

    # ------------------------------------------------------------------
    # ✅ Alignement ISO/IEC 27031:2025 — le point le plus important
    # identifié : un PRA n'avait aucun RTO/RPO cible, alors que c'est
    # précisément la donnée centrale attendue d'un plan de reprise
    # informatique. Champs ajoutés, aucun retiré/renommé.
    # ------------------------------------------------------------------

    target_rto_hours = fields.Float(string='RTO cible (heures)')

    target_rpo_hours = fields.Float(string='RPO cible (heures)')

    # ------------------------------------------------------------------
    # ✅ Lien réciproque vers les PCA associés — même relation que
    # risk.bcp.plan.drp_ids (même table), modifiable indifféremment depuis
    # l'écran PCA ou l'écran PRA. Répond directement à "pourquoi on ne voit
    # pas le PCA" quand on saisit un PRA.
    # ------------------------------------------------------------------

    bcp_ids = fields.Many2many(
        'risk.bcp.plan',
        relation='risk_bcp_drp_rel',
        column1='drp_id',
        column2='bcp_id',
        string='PCA associés',
        help="Plans de continuité métier (PCA) qui s'appuient sur ce "
             "système et donc sur ce PRA."
    )

    last_backup_test_date = fields.Date(
        string='Dernier test de restauration',
        help="Date du dernier test de restauration réel des sauvegardes — "
             "'backup_strategy' documente la stratégie, ce champ documente "
             "qu'elle a été vérifiée en pratique."
    )

    last_restore_test_result = fields.Selection(
        [
            ('success', 'Réussi'),
            ('partial', 'Partiellement réussi'),
            ('failed', 'Échoué')
        ],
        string='Résultat du dernier test'
    )

    last_review_date = fields.Date(string='Dernière revue')

    next_review_date = fields.Date(string='Prochaine revue')

    approved_date = fields.Date(string='Date d\'approbation', readonly=True)

    approved_by = fields.Many2one('res.users', string='Approuvé par', readonly=True)

    last_test_date = fields.Date(
        compute='_compute_last_test',
        string='Dernier test (exercice)'
    )

    last_tested_rto_hours = fields.Float(
        compute='_compute_last_test',
        string='Dernier RTO testé (heures)'
    )

    last_tested_rpo_hours = fields.Float(
        compute='_compute_last_test',
        string='Dernier RPO testé (heures)'
    )

    @api.depends()
    def _compute_last_test(self):
        """Même principe que risk.bcp.plan._compute_last_test : dérivé du
        plus récent exercice réalisé référençant ce PRA (risk.exercise.
        drp_id), plutôt que ressaisi à la main."""
        Exercise = self.env['risk.exercise']
        for rec in self:
            last_exercise = Exercise.search(
                [('drp_id', '=', rec.id), ('state', '=', 'completed')],
                order='exercise_date desc',
                limit=1,
            )
            rec.last_test_date = last_exercise.exercise_date if last_exercise else False
            rec.last_tested_rto_hours = last_exercise.tested_rto_hours if last_exercise else 0.0
            rec.last_tested_rpo_hours = last_exercise.tested_rpo_hours if last_exercise else 0.0

    def action_approve(self):
        """Approuver le plan de reprise après sinistre.

        Comme pour risk.bcp.plan.action_approve : ce statut alimente le taux
        de couverture PRA du tableau de bord Résilience, il doit donc passer
        par une action explicite plutôt qu'une simple liste déroulante.
        Renseigne aussi la date/l'auteur d'approbation et, si absente, une
        prochaine revue à un an."""
        for record in self:
            record.state = 'approved'
            record.approved_date = fields.Date.today()
            record.approved_by = self.env.user
            record.last_review_date = fields.Date.today()
            if not record.next_review_date:
                record.next_review_date = fields.Date.today() + timedelta(days=365)
        return True

    def action_draft(self):
        """Remettre le plan en brouillon."""
        for record in self:
            record.state = 'draft'
        return True

    # ------------------------------------------------------------------
    # ✅ "Tests du PRA" — même correctif que sur risk.bcp.plan.
    # ------------------------------------------------------------------

    test_count = fields.Integer(
        compute='_compute_test_count',
        string='Nombre de tests'
    )

    @api.depends()
    def _compute_test_count(self):
        Exercise = self.env['risk.exercise']
        for rec in self:
            rec.test_count = Exercise.search_count([('drp_id', '=', rec.id)])

    def action_view_tests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Tests du PRA - {self.name}',
            'res_model': 'risk.exercise',
            'view_mode': 'list,form',
            'domain': [('drp_id', '=', self.id)],
            'context': {'default_drp_id': self.id},
        }
