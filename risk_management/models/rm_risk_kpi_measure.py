from odoo import api, fields, models, _


class RiskKpiMeasure(models.Model):
    _name = 'risk.kpi.measure'
    _description = 'KPI Measurement'
    _order = 'measure_date desc, id desc'

    kpi_id = fields.Many2one(
        'risk.kpi',
        string='KPI',
        required=True,
        ondelete='cascade',
        index=True
    )

    measure_date = fields.Date(
        string='Date de mesure',
        required=True,
        default=fields.Date.today
    )

    value = fields.Float(
        string='Valeur',
        required=True
    )

    comment = fields.Html(
        string='Commentaire'
    )

    # ✅ Champs relatés au KPI
    kpi_name = fields.Char(
        related='kpi_id.name',
        readonly=True,
        string='KPI'
    )

    kpi_code = fields.Char(
        related='kpi_id.code',
        readonly=True,
        string='Code KPI'
    )

    # ✅ Champs pour le suivi
    created_by = fields.Many2one(
        'res.users',
        string='Créé par',
        default=lambda self: self.env.user
    )

    create_date = fields.Datetime(
        string='Date de création',
        readonly=True,
        default=fields.Datetime.now
    )

    def action_view_kpi(self):
        """Ouvre le KPI associé"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'KPI',
            'res_model': 'risk.kpi',
            'view_mode': 'form',
            'res_id': self.kpi_id.id,
            'target': 'current',
        }