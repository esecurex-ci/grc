from odoo import models, fields, api


class RiskContinuityDashboard(models.Model):
    _name = 'risk.continuity.dashboard'
    _description = 'Business Continuity Dashboard'

    name = fields.Char(
        default='Business Continuity Dashboard'
    )

    avg_rto = fields.Float(
        compute='_compute_dashboard'
    )

    avg_rpo = fields.Float(
        compute='_compute_dashboard'
    )

    avg_mtd = fields.Float(
        compute='_compute_dashboard'
    )

    exercise_count = fields.Integer(
        compute='_compute_dashboard'
    )

    bcp_coverage = fields.Float(
        compute='_compute_dashboard'
    )

    drp_coverage = fields.Float(
        compute='_compute_dashboard'
    )

    @api.depends()
    def _compute_dashboard(self):

        activities = self.env[
            'risk.bia.activity'
        ].search([])

        exercises = self.env[
            'risk.exercise'
        ].search([
            ('state', '=', 'completed')
        ])

        bcps = self.env[
            'risk.bcp.plan'
        ].search([
            ('state', '=', 'approved')
        ])

        drps = self.env[
            'risk.drp.plan'
        ].search([
            ('state', '=', 'approved')
        ])

        for rec in self:

            if activities:

                rec.avg_rto = sum(
                    activities.mapped('rto_hours')
                ) / len(activities)

                rec.avg_rpo = sum(
                    activities.mapped('rpo_hours')
                ) / len(activities)

                rec.avg_mtd = sum(
                    activities.mapped('mtd_hours')
                ) / len(activities)

            else:

                rec.avg_rto = 0
                rec.avg_rpo = 0
                rec.avg_mtd = 0

            rec.exercise_count = len(
                exercises
            )

            total_bia = self.env[
                'risk.bia'
            ].search_count([])

            rec.bcp_coverage = (
                len(bcps) * 100 / total_bia
                if total_bia else 0
            )

            rec.drp_coverage = (
                len(drps) * 100 / total_bia
                if total_bia else 0
            )