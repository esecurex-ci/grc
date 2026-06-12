from odoo import models


class RiskCrisisCommandCenter(models.Model):
    _name = 'risk.crisis.command.center'
    _description = 'Crisis Command Center'

    def get_dashboard_data(self):

        Crisis = self.env['risk.crisis']
        Action = self.env['risk.crisis.action']
        Timeline = self.env['risk.crisis.timeline']
        Warroom = self.env['risk.crisis.warroom']

        open_crises = Crisis.search([
            ('state', '!=', 'closed')
        ])

        critical_crises = Crisis.search([
            ('state', '!=', 'closed'),
            ('crisis_level', '=', 'critical')
        ])

        overdue_actions = Action.search([
            ('state', 'not in',
             ['completed', 'cancelled'])
        ])

        timeline = Timeline.search(
            [],
            order='event_date desc',
            limit=20
        )

        warrooms = Warroom.search([
            ('status', '=', 'active')
        ])

        return {
            'open_crises': len(open_crises),
            'critical_crises': len(critical_crises),
            'overdue_actions': len(overdue_actions),
            'warrooms': len(warrooms),
            'timeline': [
                {
                    'date': t.event_date,
                    'title': t.title,
                    'type': t.event_type
                }
                for t in timeline
            ]
        }