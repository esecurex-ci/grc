from odoo import models, fields, api

class RiskProcess(models.Model):
    _name = 'risk.process'
    _description = 'Business Process'

    name = fields.Char(required=True)

    code = fields.Char()

    owner_id = fields.Many2one(
        'hr.employee',
        string='Process Owner'
    )

    description = fields.Text()

    active = fields.Boolean(default=True)

    macro_process_id = fields.Many2one('risk.macro.process', string='Macro Processus')
    activity_ids = fields.One2many(
        'risk.activity',
        'process_id',
        string='Activités'
    )

    activity_count = fields.Integer(
        compute='_compute_activity_count',
        string='Nombre d\'activités'
    )

    risk_count = fields.Integer(
        compute='_compute_risk_count',
        string='Nombre de risques'
    )

    # =====================================================
    # MÉTHODES DE CALCUL
    # =====================================================

    @api.depends('activity_ids')
    def _compute_activity_count(self):
        for record in self:
            record.activity_count = len(record.activity_ids)

    @api.depends('activity_ids', 'activity_ids.risk_ids')
    def _compute_risk_count(self):
        for record in self:
            risks = record.activity_ids.mapped('risk_ids')
            record.risk_count = len(risks)

    # =====================================================
    # MÉTHODES D'ACTION
    # =====================================================

    def action_view_activities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Activités',
            'res_model': 'risk.activity',
            'view_mode': 'tree,form',
            'domain': [('process_id', '=', self.id)],
            'context': {'default_process_id': self.id},
        }

    def action_view_risks(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Risques',
            'res_model': 'risk.risk',
            'view_mode': 'tree,form',
            'domain': [('process_id', '=', self.id)],
            'context': {'default_process_id': self.id},
        }
