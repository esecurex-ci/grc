from odoo import models, fields


class RiskBcpResource(models.Model):
    _name = 'risk.bcp.resource'
    _description = 'BCP Resource'

    bcp_id = fields.Many2one(
        'risk.bcp.plan',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        required=True
    )

    resource_type = fields.Selection(
        [
            ('human', 'Human'),
            ('application', 'Application'),
            ('server', 'Server'),
            ('facility', 'Facility'),
            ('provider', 'Provider')
        ]
    )

    description = fields.Html()

    # ------------------------------------------------------------------
    # ✅ Alignement ISO 22301 §8.4 — équipe de continuité / contacts
    # d'escalade structurés, en plus (et non à la place) de 'name' et
    # 'description' déjà utilisés. Ces champs sont facultatifs : les
    # ressources déjà saisies restent valables sans y renseigner quoi que
    # ce soit.
    # ------------------------------------------------------------------

    role = fields.Char(
        string='Rôle',
        help="Rôle dans l'équipe de continuité (ex. Coordinateur de "
             "crise, Suppléant) — pertinent surtout quand resource_type "
             "= Human."
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Collaborateur',
        help="Lien vers la personne réelle, quand resource_type = Human."
    )

    partner_id = fields.Many2one(
        'res.partner',
        string='Fournisseur / prestataire',
        help="Lien vers le partenaire réel, quand resource_type = Provider."
    )

    contact_info = fields.Char(
        string='Contact d\'urgence',
        help="Téléphone/email d'astreinte — un PCA doit rester exploitable "
             "même si les systèmes habituels (annuaire interne) sont "
             "indisponibles."
    )