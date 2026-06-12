from odoo import models, fields, api


class RiskBia(models.Model):
    _name = 'risk.bia'
    _description = 'Business Impact Analysis'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(required=True)
    description = fields.Html()
    process_id = fields.Many2one('risk.process',required=True)
    owner_id = fields.Many2one('hr.employee')
    assessment_date = fields.Date()
    state = fields.Selection([ ('draft', 'Draft'),('validated', 'Validated')], default='draft')
    activity_ids = fields.One2many(
        'risk.bia.activity',
        'bia_id',
        string='Activities'
    )

    activity_count = fields.Integer(
        compute='_compute_activity_count'
    )

    @api.depends('activity_ids')
    def _compute_activity_count(self):
        for rec in self:
            rec.activity_count = len(
                rec.activity_ids
            )

    def action_view_activities(self):
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Critical Activities',
            'res_model': 'risk.bia.activity',
            'view_mode': 'list,form',
            'domain': [
                ('bia_id', '=', self.id)
            ],
            'context': {
                'default_bia_id': self.id
            }
        }