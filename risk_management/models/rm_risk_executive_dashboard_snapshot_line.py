from odoo import models, fields


class RiskExecutiveDashboardSnapshotLine(models.Model):
    _name = 'risk.executive.dashboard.snapshot.line'
    _description = 'Executive Dashboard Snapshot Line'

    snapshot_id = fields.Many2one(
        'risk.executive.dashboard.snapshot',
        required=True,
        ondelete='cascade'
    )

    category = fields.Selection(
        [
            ('risk', 'Risk'),
            ('incident', 'Incident'),
            ('audit', 'Audit'),
            ('compliance', 'Compliance'),
            ('resilience', 'Resilience'),
            ('cyber', 'Cyber')
        ],
        required=True
    )

    code = fields.Char(
        required=True
    )

    name = fields.Char(
        required=True
    )

    value = fields.Float()

    target = fields.Float()

    variance = fields.Float()

    status = fields.Selection(
        [
            ('green', 'Green'),
            ('amber', 'Amber'),
            ('red', 'Red')
        ]
    )

    comment = fields.Text()