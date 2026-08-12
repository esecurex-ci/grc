from odoo import api, models, fields


class RiskBcpPlanVersion(models.Model):
    _name = 'risk.bcp.plan.version'
    _description = 'Version historique d\'un PCA'
    _order = 'bcp_id, version_number desc'
    _rec_name = 'version_label'

    # ------------------------------------------------------------------
    # ✅ Alignement ISO 22301 §8.4 : "le PCA a un caractère évolutif, donc on
    # doit tenir compte de sa mise à jour" — un risk.bcp.plan est un
    # enregistrement mutable unique ; sans historique, une version révisée
    # écrase silencieusement le contenu précédemment approuvé, ce qui rend
    # impossible de savoir "que disait le plan approuvé le jour où il a été
    # testé/activé".
    #
    # Ce modèle capture un instantané en lecture (contenu figé au moment de
    # la révision) créé automatiquement par risk.bcp.plan.action_revise(),
    # jamais modifié par l'utilisateur ensuite (sauf le champ 'changelog',
    # qui reste éditable pour documenter le motif de la révision).
    #
    # Volontairement distinct de risk.document.version (qui exige un fichier
    # attaché obligatoire) : un PCA est un enregistrement structuré Odoo, pas
    # un document externe, donc un modèle dédié et plus simple convient
    # mieux ici plutôt que de forcer un attachment_id sans objet.
    # ------------------------------------------------------------------

    bcp_id = fields.Many2one(
        'risk.bcp.plan',
        string='PCA',
        required=True,
        ondelete='cascade',
        index=True
    )

    version_number = fields.Integer(
        string='Version',
        required=True
    )

    version_label = fields.Char(
        compute='_compute_version_label',
        store=True,
        string='Libellé'
    )

    snapshot_date = fields.Date(
        string='Date de révision',
        default=fields.Date.today,
        readonly=True
    )

    author_id = fields.Many2one(
        'res.users',
        string='Révisé par',
        readonly=True
    )

    state_at_snapshot = fields.Char(
        string='Statut au moment de la révision',
        readonly=True
    )

    target_rto_hours_snapshot = fields.Float(
        string='RTO cible (à cette version)',
        readonly=True
    )

    activation_criteria_snapshot = fields.Html(
        string='Critères d\'activation (à cette version)',
        readonly=True
    )

    recovery_strategy_snapshot = fields.Html(
        string='Stratégie de reprise (à cette version)',
        readonly=True
    )

    communication_plan_snapshot = fields.Html(
        string='Plan de communication (à cette version)',
        readonly=True
    )

    changelog = fields.Text(
        string='Motif de la révision',
        help="Ce que cette révision a changé — reste éditable après "
             "création pour documenter le motif, à la différence des "
             "champs 'snapshot' ci-dessus qui restent figés."
    )

    @api.depends('version_number')
    def _compute_version_label(self):
        for rec in self:
            rec.version_label = f"v{rec.version_number}"
