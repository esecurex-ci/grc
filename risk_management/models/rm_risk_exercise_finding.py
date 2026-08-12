from odoo import models, fields


class RiskExerciseFinding(models.Model):
    _name = 'risk.exercise.finding'
    _description = 'Exercise Finding'

    exercise_id = fields.Many2one(
        'risk.exercise',
        required=True,
        ondelete='cascade'
    )

    description = fields.Html()

    severity = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical')
        ]
    )

    recommendation = fields.Html(string='Recommendation')

    # ------------------------------------------------------------------
    # ✅ Alignement ISO 22398 — un constat d'exercice doit être suivi
    # jusqu'à sa clôture, sur le même principe déjà utilisé dans ce
    # module pour risk.audit.recommendation. Champ 'state' ajouté avec
    # une valeur par défaut ('open') : Odoo réapplique un default statique
    # aux lignes déjà existantes lors de la mise à jour du module, donc les
    # constats déjà saisis ne restent pas à une valeur vide/incohérente.
    # ------------------------------------------------------------------

    responsible_id = fields.Many2one(
        'hr.employee',
        string='Responsable de l\'action corrective'
    )

    target_date = fields.Date(
        string='Date cible de clôture'
    )

    state = fields.Selection(
        [
            ('open', 'Ouvert'),
            ('in_progress', 'En cours'),
            ('closed', 'Clôturé'),
        ],
        string='Statut',
        default='open'
    )