from odoo import models, fields, api


class RiskIncident(models.Model):
    _name = 'risk.incident'
    _description = 'Risk Incident'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]
    _order = 'incident_date desc'

    name = fields.Char(
        readonly=True,
        default='New'
    )

    title = fields.Char(
        required=True,
        tracking=True
    )

    description = fields.Html()

    incident_date = fields.Datetime(
        required=True,
        tracking=True
    )

    detection_date = fields.Datetime()

    declaration_date = fields.Datetime(
        default=fields.Datetime.now
    )

    category_id = fields.Many2one(
        'risk.incident.category'
    )

    type_id = fields.Many2one(
        'risk.incident.type'
    )

    risk_id = fields.Many2one(
        'risk.risk',
        required=True,
        tracking=True
    )

    owner_id = fields.Many2one(
        'hr.employee',
        string='Incident Owner'
    )

    reporter_id = fields.Many2one(
        'hr.employee',
        string='Reporter'
    )

    company_id = fields.Many2one(
        'res.company',
        default=lambda self:
        self.env.company
    )

    severity = fields.Selection(
        [
            ('low', 'Low'),
            ('moderate', 'Moderate'),
            ('high', 'High'),
            ('critical', 'Critical')
        ],
        default='moderate'
    )

    status = fields.Selection(
        [
            ('draft', 'Draft'),
            ('declared', 'Declared'),
            ('investigation', 'Investigation'),
            ('action_plan', 'Action Plan'),
            ('closed', 'Closed')
        ],
        default='draft',
        tracking=True
    )

    root_cause_ids = fields.One2many(
        'risk.root.cause',
        'incident_id'
    )

    loss_ids = fields.One2many(
        'risk.loss',
        'incident_id'
    )

    corrective_action_ids = fields.One2many(
        'risk.corrective.action',
        'incident_id'
    )

    total_loss = fields.Monetary(
        compute='_compute_total_loss',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self:
        self.env.company.currency_id
    )
    market_impact = fields.Boolean()

    regulatory_notification = fields.Boolean()

    regulator_notified_date = fields.Date()

    @api.depends('loss_ids.amount')
    def _compute_total_loss(self):

        for rec in self:

            rec.total_loss = sum(
                rec.loss_ids.mapped('amount')
            )

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            if vals.get('name', 'New') == 'New':

                vals['name'] = self.env[
                    'ir.sequence'
                ].next_by_code(
                    'risk.incident'
                )

        return super().create(vals_list)

    def action_declare(self):
        self.write({
            'status': 'declared'
        })

    def action_investigate(self):
        self.write({
            'status': 'investigation'
        })

    def action_action_plan(self):
        self.write({
            'status': 'action_plan'
        })

    def action_close(self):
        self.write({
            'status': 'closed'
        })