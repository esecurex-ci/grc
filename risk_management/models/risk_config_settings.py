# models/risk_config_settings.py

from odoo import models, fields, api


class RiskConfigSettings(models.TransientModel):
    _name = 'risk.config.settings'
    _description = 'Paramètres des échelles de risque'
    _inherit = 'res.config.settings'

    scale_probability_ids = fields.Many2many(
        'risk.scale.value',
        'risk_config_scale_probability_rel',
        'config_id', 'scale_id',
        domain="[('scale_type', '=', 'probability')]",
        string='Échelle de probabilité'
    )

    scale_impact_ids = fields.Many2many(
        'risk.scale.value',
        'risk_config_scale_impact_rel',
        'config_id', 'scale_id',
        domain="[('scale_type', '=', 'impact')]",
        string='Échelle d\'impact'
    )

    scale_level_ids = fields.Many2many(
        'risk.scale.value',
        'risk_config_scale_level_rel',
        'config_id', 'scale_id',
        domain="[('scale_type', '=', 'level')]",
        string='Échelle des niveaux de risque'
    )

    @api.model
    def get_values(self):
        """Récupère les valeurs par défaut"""
        res = super().get_values()
        config = self.env['risk.config.settings'].search([], limit=1)
        if config:
            res.update({
                'scale_probability_ids': [(6, 0, config.scale_probability_ids.ids)],
                'scale_impact_ids': [(6, 0, config.scale_impact_ids.ids)],
                'scale_level_ids': [(6, 0, config.scale_level_ids.ids)],
            })
        return res

    def set_values(self):
        """Sauvegarde les valeurs"""
        super().set_values()
        config = self.env['risk.config.settings'].search([], limit=1)
        if not config:
            config = self.env['risk.config.settings'].create({})

        config.write({
            'scale_probability_ids': [(6, 0, self.scale_probability_ids.ids)],
            'scale_impact_ids': [(6, 0, self.scale_impact_ids.ids)],
            'scale_level_ids': [(6, 0, self.scale_level_ids.ids)],
        })