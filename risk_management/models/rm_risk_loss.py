from odoo import models, fields, api


class RiskLoss(models.Model):
    _name = 'risk.loss'
    _description = 'Operational Loss'

    incident_id = fields.Many2one(
        'risk.incident',
        required=True,
        ondelete='cascade'
    )

    date = fields.Date(
        required=True
    )

    description = fields.Char()

    amount = fields.Monetary(
        required=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self:
        self.env.company.currency_id
    )

    recovered_amount = fields.Monetary()

    net_loss = fields.Monetary(
        compute='_compute_net_loss',
        store=True
    )

    @api.depends(
        'amount',
        'recovered_amount'
    )
    def _compute_net_loss(self):

        for rec in self:

            rec.net_loss = (
                rec.amount -
                rec.recovered_amount
            )