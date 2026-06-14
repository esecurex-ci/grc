from odoo import models, fields


class RiskCrisisWarroom(models.Model):
    _name = 'risk.crisis.warroom'
    _description = 'Crisis War Room'

    crisis_id = fields.Many2one(
        'risk.crisis',
        required=True
    )

    activation_date = fields.Datetime()

    location = fields.Char()

    meeting_url = fields.Char()

    status = fields.Selection(
        [
            ('inactive', 'Inactive'),
            ('active', 'Active'),
            ('closed', 'Closed')
        ],
        default='inactive'
    )

    notes = fields.Html()

    # ⬇️ CE CHAMP EST OBLIGATOIRE ⬇️
    crisis_id = fields.Many2one(
        'risk.crisis',
        string='Crisis',
        required=True,
        ondelete='cascade'
    )

    # ⬇️ CE CHAMP state DOIT EXISTER ⬇️
    state = fields.Selection([
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('closed', 'Closed')
    ], string='Status', default='planned')