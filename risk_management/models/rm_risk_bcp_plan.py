from datetime import timedelta

from odoo import models, fields, api


class RiskBcpPlan(models.Model):
    _name = 'risk.bcp.plan'
    _description = 'Business Continuity Plan'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    process_id = fields.Many2one(
        'risk.process'
    )

    owner_id = fields.Many2one(
        'hr.employee'
    )

    activation_criteria = fields.Html()

    recovery_strategy = fields.Html()

    communication_plan = fields.Html()

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('obsolete', 'Obsolete')
        ],
        default='draft',
        tracking=True
    )

    # ------------------------------------------------------------------
    # ✅ Alignement ISO 22301 §8.4 — champs ajoutés (aucun retiré/renommé).
    # ------------------------------------------------------------------

    bia_id = fields.Many2one(
        'risk.bia',
        string='BIA de référence',
        help="Traçabilité attendue par ISO 22301 : un PCA doit se fonder "
             "sur une analyse d'impact (BIA) identifiée. Champ facultatif "
             "pour ne pas bloquer les plans déjà créés sans BIA associée."
    )

    target_rto_hours = fields.Float(
        string='RTO cible (heures)',
        tracking=True,
        help="Délai de reprise visé par CE plan — à comparer au RTO "
             "effectivement atteint lors des exercices (voir "
             "'Dernier RTO testé' ci-dessous)."
    )

    # ------------------------------------------------------------------
    # ✅ Lien réciproque vers les PRA associés — auparavant, un PRA ne
    # référençait rien qui permette de savoir quel(s) PCA il supporte, et
    # inversement un PCA ne montrait aucun PRA. Même table de relation
    # utilisée des deux côtés (drp_ids ici, bcp_ids sur risk.drp.plan) pour
    # que ce soit une seule et même relation, modifiable depuis l'un ou
    # l'autre écran.
    # ------------------------------------------------------------------

    drp_ids = fields.Many2many(
        'risk.drp.plan',
        relation='risk_bcp_drp_rel',
        column1='bcp_id',
        column2='drp_id',
        string='PRA associés',
        help="Plans de reprise (PRA) des systèmes IT sur lesquels ce PCA "
             "s'appuie."
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

    @api.depends()
    def _compute_last_test(self):
        """Dérive la date et le RTO du dernier test réel, à partir du plus
        récent exercice réalisé qui référence ce PCA (risk.exercise.bcp_id).
        Calculé plutôt que saisi à la main, pour éviter une double saisie
        qui pourrait diverger de ce que les exercices ont réellement
        enregistré."""
        Exercise = self.env['risk.exercise']
        for rec in self:
            last_exercise = Exercise.search(
                [('bcp_id', '=', rec.id), ('state', '=', 'completed')],
                order='exercise_date desc',
                limit=1,
            )
            rec.last_test_date = last_exercise.exercise_date if last_exercise else False
            rec.last_tested_rto_hours = last_exercise.tested_rto_hours if last_exercise else 0.0

    # ------------------------------------------------------------------
    # ✅ "Tests du PCA" — le lien risk.exercise.bcp_id existait déjà (utilisé
    # par _compute_last_test ci-dessus) mais n'était visible/accessible
    # depuis nulle part sur la fiche du PCA : impossible de voir OU de créer
    # les exercices qui le testent sans aller chercher dans le menu
    # Exercices et sélectionner le bon PCA à la main.
    # ------------------------------------------------------------------

    test_count = fields.Integer(
        compute='_compute_test_count',
        string='Nombre de tests'
    )

    @api.depends()
    def _compute_test_count(self):
        Exercise = self.env['risk.exercise']
        for rec in self:
            rec.test_count = Exercise.search_count([('bcp_id', '=', rec.id)])

    def action_view_tests(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Tests du PCA - {self.name}',
            'res_model': 'risk.exercise',
            'view_mode': 'list,form',
            'domain': [('bcp_id', '=', self.id)],
            'context': {'default_bcp_id': self.id},
        }

    # ------------------------------------------------------------------
    # ✅ Caractère évolutif du PCA (ISO 22301) — un PCA approuvé qui doit
    # être mis à jour ne doit pas voir son contenu précédemment approuvé
    # silencieusement écrasé : action_revise() figure un instantané du
    # contenu actuel dans risk.bcp.plan.version avant de rouvrir le plan en
    # brouillon pour édition. L'historique complet reste consultable via le
    # bouton "Historique".
    # ------------------------------------------------------------------

    version_number = fields.Integer(
        string='Version',
        default=1,
        readonly=True
    )

    version_ids = fields.One2many(
        'risk.bcp.plan.version',
        'bcp_id',
        string='Historique des versions'
    )

    version_count = fields.Integer(
        compute='_compute_version_count'
    )

    @api.depends('version_ids')
    def _compute_version_count(self):
        for rec in self:
            rec.version_count = len(rec.version_ids)

    def action_revise(self):
        """Archive le contenu actuellement approuvé dans une nouvelle ligne
        d'historique, puis rouvre le plan en brouillon pour édition — au
        lieu de laisser une modification directe écraser silencieusement ce
        qui avait été approuvé (et potentiellement déjà testé/exercé)."""
        for record in self:
            self.env['risk.bcp.plan.version'].create({
                'bcp_id': record.id,
                'version_number': record.version_number,
                'author_id': self.env.user.id,
                'state_at_snapshot': record.state,
                'target_rto_hours_snapshot': record.target_rto_hours,
                'activation_criteria_snapshot': record.activation_criteria,
                'recovery_strategy_snapshot': record.recovery_strategy,
                'communication_plan_snapshot': record.communication_plan,
            })
            record.version_number += 1
            record.state = 'draft'
        return True

    def action_view_versions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Historique des versions - {self.name}',
            'res_model': 'risk.bcp.plan.version',
            'view_mode': 'list,form',
            'domain': [('bcp_id', '=', self.id)],
        }

    def action_approve(self):
        """Approuver le plan de continuité.

        Auparavant, 'state' n'était modifiable que via une liste déroulante
        libre dans le corps du formulaire : n'importe qui pouvait faire
        passer un PCA à 'Approved' sans étape de validation, alors que ce
        même statut alimente directement le taux de couverture PCA affiché
        au tableau de bord Résilience et au Cockpit. Ce bouton (et les deux
        suivants) rétablit un vrai circuit de validation, sur le même
        principe que risk.bia.action_approve. Renseigne aussi la date/
        l'auteur d'approbation et, si absente, une prochaine revue à un an."""
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

    def action_obsolete(self):
        """Marquer le plan comme obsolète (remplacé par une nouvelle version,
        processus supprimé, etc.)."""
        for record in self:
            record.state = 'obsolete'
        return True

    resource_ids = fields.One2many(
        'risk.bcp.resource',
        'bcp_id'
    )
    resource_count = fields.Integer(
        compute='_compute_resource_count'
    )

    @api.depends('resource_ids')
    def _compute_resource_count(self):
        for rec in self:
            rec.resource_count = len(
                rec.resource_ids
            )

    def action_view_resources(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Resources',
            'res_model': 'risk.bcp.resource',
            'view_mode': 'list,form',
            'domain': [
                ('bcp_id', '=', self.id)
            ],
            'context': {
                'default_bcp_id': self.id
            }
        }