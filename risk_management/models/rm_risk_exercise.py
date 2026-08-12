from odoo import models, fields, api


class RiskExercise(models.Model):
    _name = 'risk.exercise'
    _description = 'BCP/DRP Exercise'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]

    name = fields.Char(
        required=True
    )

    exercise_date = fields.Date()

    exercise_type = fields.Selection(
        [
            ('tabletop', 'Table Top'),
            ('simulation', 'Simulation'),
            ('full_scale', 'Full Scale')
        ]
    )

    scenario_id = fields.Many2one(
        'risk.crisis.scenario'
    )

    objective = fields.Html()

    result = fields.Html()

    state = fields.Selection(
        [
            ('planned', 'Planned'),
            ('completed', 'Completed')
        ],
        default='planned'
    )

    # ------------------------------------------------------------------
    # ✅ Alignement ISO 22398 — champs ajoutés (aucun retiré/renommé).
    # Ces liens permettent à risk.bcp.plan / risk.drp.plan de calculer
    # automatiquement leur "dernier test" (last_test_date /
    # last_tested_rto_hours / last_tested_rpo_hours) à partir du plus
    # récent exercice réalisé qui les référence.
    # ------------------------------------------------------------------

    bcp_id = fields.Many2one(
        'risk.bcp.plan',
        string='PCA testé',
        help="Plan de continuité que cet exercice a testé, s'il y a lieu."
    )

    drp_id = fields.Many2one(
        'risk.drp.plan',
        string='PRA testé',
        help="Plan de reprise que cet exercice a testé, s'il y a lieu."
    )

    tested_rto_hours = fields.Float(
        string='RTO atteint lors de l\'exercice (heures)'
    )

    tested_rpo_hours = fields.Float(
        string='RPO atteint lors de l\'exercice (heures)'
    )

    participant_ids = fields.Many2many(
        'hr.employee',
        string='Participants'
    )

    def action_complete(self):
        """Marquer l'exercice comme réalisé.

        Le nombre d'exercices 'completed' pilote directement le taux de
        réussite des exercices affiché au tableau de bord Résilience et au
        Cockpit : ce passage à 'completed' doit donc être une action
        explicite (posée une fois les résultats/constats renseignés), et non
        un simple choix dans une liste déroulante."""
        for record in self:
            record.state = 'completed'
        return True

    def action_reset_planned(self):
        """Remettre l'exercice à l'état planifié (ex. ré-ouverture après une
        clôture prématurée)."""
        for record in self:
            record.state = 'planned'
        return True

    finding_ids = fields.One2many(
        'risk.exercise.finding',
        'exercise_id'
    )
    finding_count = fields.Integer(
        compute='_compute_finding_count'
    )

    @api.depends('finding_ids')
    def _compute_finding_count(self):
        for rec in self:
            rec.finding_count = len(
                rec.finding_ids
            )

    def action_view_findings(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Exercise Findings',
            'res_model': 'risk.exercise.finding',
            'view_mode': 'list,form',
            'domain': [
                ('exercise_id', '=', self.id)
            ],
            'context': {
                'default_exercise_id': self.id
            }
        }