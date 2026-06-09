from odoo import models, fields


class RiskBia(models.Model):
    _name = 'risk.bia'
    _description = 'Business Impact Analysis'


    name = fields.Char(required=True)
    description = fields.Html()
    process_id = fields.Many2one('risk.process',required=True)
    owner_id = fields.Many2one('hr.employee')
    assessment_date = fields.Date()
    state = fields.Selection([ ('draft', 'Draft'),('validated', 'Validated')], default='draft')
    activity_ids = fields.One2many('risk.bia.activity','bia_id')