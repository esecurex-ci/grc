from odoo import models, fields


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