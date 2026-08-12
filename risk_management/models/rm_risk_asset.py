from odoo import models, fields

class RiskAsset(models.Model):
    _name = 'risk.asset'
    _description = 'Actif'

    name = fields.Char(string='Nom', required=True)

    code = fields.Char(string='Code')

    asset_type = fields.Selection([
        ('application', 'Application'),
        ('server', 'Serveur'),
        ('database', 'Base de données'),
        ('network', 'Réseau'),
        ('cloud', 'Cloud'),
        ('other', 'Autre'),
    ], string='Type d\'actif')

    description = fields.Text(string='Description')

    active = fields.Boolean(string='Actif', default=True)

    # ------------------------------------------------------------------
    # ✅ Alignement ISO/IEC 27031:2025 — sans niveau de criticité, il est
    # impossible de prioriser objectivement quels actifs couvrir en
    # premier par un PRA. Champ facultatif (pas de valeur par défaut
    # imposée) : les actifs déjà créés restent valables sans classification.
    # ------------------------------------------------------------------

    criticality_tier = fields.Selection(
        [
            ('tier1', 'Tier 1 - Critique'),
            ('tier2', 'Tier 2 - Élevé'),
            ('tier3', 'Tier 3 - Moyen'),
            ('tier4', 'Tier 4 - Faible'),
        ],
        string='Niveau de criticité'
    )

    process_ids = fields.Many2many(
        'risk.process',
        string='Processus utilisant cet actif',
        help="Ferme le lien manquant entre le PRA (qui protège un actif "
             "IT) et le processus métier qui en dépend réellement — sans "
             "ce lien, l'urgence réelle d'un actif non couvert reste "
             "invisible."
    )
