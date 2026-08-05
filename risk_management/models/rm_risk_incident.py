from odoo import models, fields, api


class RiskIncident(models.Model):
    _name = 'risk.incident'
    _description = 'Incident de risque'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin'
    ]
    _order = 'incident_date desc'

    name = fields.Char(
        string='Référence',
        readonly=True,
        default='New'
    )

    title = fields.Char(
        string='Titre',
        required=True,
        tracking=True
    )

    description = fields.Html(string='Description')

    incident_date = fields.Datetime(
        string="Date de l'incident",
        required=True,
        tracking=True
    )

    detection_date = fields.Datetime(string='Date de détection')

    declaration_date = fields.Datetime(
        string='Date de déclaration',
        default=fields.Datetime.now
    )

    category_id = fields.Many2one(
        'risk.incident.category',
        string='Catégorie'
    )

    type_id = fields.Many2one(
        'risk.incident.type',
        string="Type d'incident"
    )

    risk_id = fields.Many2one(
        'risk.risk',
        string='Risque',
        required=True,
        tracking=True
    )

    owner_id = fields.Many2one(
        'hr.employee',
        string='Responsable'
    )

    reporter_id = fields.Many2one(
        'hr.employee',
        string='Déclarant'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self:
        self.env.company
    )

    severity = fields.Selection(
        [
            ('low', 'Faible'),
            ('moderate', 'Modérée'),
            ('high', 'Élevée'),
            ('critical', 'Critique')
        ],
        string='Gravité',
        default='moderate'
    )

    status = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('declared', 'Déclaré'),
            ('investigation', 'En investigation'),
            ('action_plan', "Plan d'action"),
            ('closed', 'Clôturé')
        ],
        string='Statut',
        default='draft',
        tracking=True
    )

    root_cause_ids = fields.One2many(
        'risk.root.cause',
        'incident_id',
        string='Causes racines'
    )

    loss_ids = fields.One2many(
        'risk.loss',
        'incident_id',
        string='Pertes'
    )

    corrective_action_ids = fields.One2many(
        'risk.corrective.action',
        'incident_id',
        string='Actions correctives'
    )

    total_loss = fields.Monetary(
        string='Perte totale',
        compute='_compute_total_loss',
        store=True
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self:
        self.env.company.currency_id
    )
    market_impact = fields.Boolean(string='Impact sur le marché')

    regulatory_notification = fields.Boolean(string='Notification réglementaire')

    regulator_notified_date = fields.Date(string='Date de notification au régulateur')
    root_cause_count = fields.Integer(
        string='Nombre de causes racines',
        compute='_compute_statistics'
    )

    loss_count = fields.Integer(
        string='Nombre de pertes',
        compute='_compute_statistics'
    )

    corrective_action_count = fields.Integer(
        string="Nombre d'actions correctives",
        compute='_compute_statistics'
    )

    action_ids = fields.Many2many(
        'risk.corrective.action',
        'risk_incident_action_rel',
        'incident_id',
        'action_id',
        string='Actions correctives'
    )

    # Statistiques
    action_count = fields.Integer(
        compute='_compute_action_stats',
        string="Nombre d'actions"
    )

    action_done_count = fields.Integer(
        compute='_compute_action_stats',
        string="Actions terminées"
    )

    @api.depends('action_ids', 'action_ids.state')
    def _compute_action_stats(self):
        for record in self:
            record.action_count = len(record.action_ids)
            record.action_done_count = len(record.action_ids.filtered(lambda a: a.state == 'done'))

    @api.depends('root_cause_ids','loss_ids','corrective_action_ids')
    def _compute_statistics(self):
        for rec in self:
            rec.root_cause_count = len(
                rec.root_cause_ids
            )

            rec.loss_count = len(
                rec.loss_ids
            )

            rec.corrective_action_count = len(
                rec.corrective_action_ids
            )

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

    def action_view_root_causes(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Causes racines',
            'res_model': 'risk.root.cause',
            'view_mode': 'list,form',
            'domain': [('incident_id', '=', self.id)],
            'context': {
                'default_incident_id': self.id
            }
        }

    def action_view_losses(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Pertes',
            'res_model': 'risk.loss',
            'view_mode': 'list,form',
            'domain': [('incident_id', '=', self.id)],
            'context': {
                'default_incident_id': self.id
            }
        }

    def action_view_corrective_actions(self):

        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Actions correctives',
            'res_model': 'risk.corrective.action',
            'view_mode': 'list,form',
            'domain': [('incident_id', '=', self.id)],
            'context': {
                'default_incident_id': self.id
            }
        }