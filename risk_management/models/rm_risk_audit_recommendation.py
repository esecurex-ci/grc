from odoo import models, fields


class RiskAuditRecommendation(models.Model):
    _name = 'risk.audit.recommendation'
    _description = 'Audit Recommendation'

    finding_id = fields.Many2one(
        'risk.audit.finding',
        required=True,
        ondelete='cascade'
    )

    description = fields.Html(
        required=True
    )

    owner_id = fields.Many2one(
        'hr.employee'
    )

    target_date = fields.Date()

    priority = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical')
        ]
    )

    state = fields.Selection(
        [
            ('open', 'Open'),
            ('implemented', 'Implemented'),
            ('verified', 'Verified'),
            ('closed', 'Closed')
        ],
        default='open'
    )

    action_plan_ids = fields.One2many(
        'risk.audit.action.plan',
        'recommendation_id'
    )
    regulation_ids = fields.Many2many(
        'risk.regulation'
    )