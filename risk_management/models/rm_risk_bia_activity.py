from odoo import models, fields


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