from odoo import models, fields, api


class RiskBiaActivity(models.Model):
    _name = 'risk.bia.activity'
    _description = 'Critical Activity'

    bia_id = fields.Many2one('risk.bia', required=True, ondelete='cascade')
    name = fields.Char(required=True)
    description = fields.Html()
    criticality = fields.Selection( [ ('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')])
    rto_hours = fields.Float(string='RTO (Hours)')
    rpo_hours = fields.Float(string='RPO (Hours)')
    mtd_hours = fields.Float(string='MTD (Hours)')
    dependency = fields.Html()
    financial_impact = fields.Monetary()
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self:
        self.env.company.currency_id
    )

    # ------------------------------------------------------------------
    # ✅ Alignement ISO/TS 22317 — 'dependency' (texte libre) est conservé
    # tel quel pour ne rien casser, et complété par des liens réels vers
    # les ressources dont dépend l'activité (ressources IT, personnes,
    # fournisseurs), comme attendu d'une cartographie de dépendances.
    # ------------------------------------------------------------------

    asset_ids = fields.Many2many(
        'risk.asset',
        string='Actifs IT dépendants',
        help="Systèmes/applications dont dépend cette activité critique."
    )

    employee_ids = fields.Many2many(
        'hr.employee',
        string='Personnes clés',
        help="Collaborateurs dont la disponibilité est indispensable à "
             "cette activité (compétences critiques)."
    )

    supplier_ids = fields.Many2many(
        'res.partner',
        string='Fournisseurs / prestataires clés'
    )

    # ------------------------------------------------------------------
    # ⚠️ Indicateur NON BLOQUANT (pas de contrainte @api.constrains) : un
    # RTO supérieur au MTD est logiquement incohérent (on ne peut pas
    # tolérer une interruption plus longue que ce qu'on juge tolérable),
    # mais bloquer l'enregistrement risquerait de casser la saisie sur des
    # données existantes déjà non conformes créées avant ce contrôle. Le
    # signal reste visible (badge liste + KPI tableau de bord) sans jamais
    # empêcher de sauvegarder.
    # ------------------------------------------------------------------

    rto_exceeds_mtd = fields.Boolean(
        string='RTO > MTD (incohérent)',
        compute='_compute_rto_exceeds_mtd',
        store=True,
        help="Le RTO saisi dépasse le MTD : incohérence à corriger, "
             "signalée sans bloquer la sauvegarde."
    )

    @api.depends('rto_hours', 'mtd_hours')
    def _compute_rto_exceeds_mtd(self):
        for rec in self:
            rec.rto_exceeds_mtd = bool(
                rec.mtd_hours and rec.rto_hours and rec.rto_hours > rec.mtd_hours
            )