from odoo import models, fields, api


class RiskCrisisLessonsLearnedDashboard(models.Model):
    _name = 'risk.crisis.lessons.learned.dashboard'
    _description = 'Lessons Learned Dashboard'

    name = fields.Char(
        default='Lessons Learned Dashboard'
    )

    total_rex = fields.Integer(
        compute='_compute_dashboard'
    )

    implemented_rex = fields.Integer(
        compute='_compute_dashboard'
    )

    pending_rex = fields.Integer(
        compute='_compute_dashboard'
    )

    implementation_rate = fields.Float(
        compute='_compute_dashboard'
    )

    @api.depends()
    def _compute_dashboard(self):

        Rex = self.env['risk.crisis.rex']

        for rec in self:

            total = Rex.search_count([])

            implemented = Rex.search_count([
                ('completion_status', '=', 'implemented')
            ])

            rec.total_rex = total

            rec.implemented_rex = implemented

            rec.pending_rex = total - implemented

            rec.implementation_rate = (
                implemented * 100 / total
                if total else 0
            )