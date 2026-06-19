from odoo import models, fields, api


class RiskBia(models.Model):
    _name = 'risk.bia'
    _description = 'Business Impact Analysis'
    _inherit = ['mail.thread',]  # Enlever 'mail.activity.mixin'

    name = fields.Char(required=True)
    description = fields.Html()
    process_id = fields.Many2one('risk.process', required=True)
    owner_id = fields.Many2one('hr.employee')
    assessment_date = fields.Date()

    # CORRECTION : Utiliser 'approved' au lieu de 'validated'
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),  # Changé de 'validated' à 'approved'
        ('archived', 'Archived')  # Ajouté pour action_archive
    ], default='draft')

    activity_ids = fields.One2many('risk.bia.activity', 'bia_id', string='Activities')
    activity_count = fields.Integer(compute='_compute_activity_count')
    mtd = fields.Integer(string='MTD (heures)', help='Maximum Tolerable Downtime')
    rto = fields.Integer(string='RTO (heures)', help='Recovery Time Objective')
    rpo = fields.Integer(string='RPO (heures)', help='Recovery Point Objective')
    priority = fields.Selection(
        [
            ('1', 'Very Low'),
            ('2', 'Low'),
            ('3', 'Medium'),
            ('4', 'High'),
            ('5', 'Critical')
        ],
        string='Priority',
        compute='_compute_priority',
        store=True
    )

    impact_operational = fields.Selection(
        [
            ('1', 'Très faible'),
            ('2', 'Faible'),
            ('3', 'Moyen'),
            ('4', 'Élevé'),
            ('5', 'Critique')
        ],
        string='Impact Opérationnel',
        required=True,
        default='1',
        help='Impact sur les opérations quotidiennes'
    )

    impact_financial = fields.Selection(
        [
            ('1', 'Très faible'),
            ('2', 'Faible'),
            ('3', 'Moyen'),
            ('4', 'Élevé'),
            ('5', 'Critique')
        ],
        string='Impact Financier',
        required=True,
        default='1',
        help='Impact financier estimé'
    )

    def action_approve(self):
        """Approuver l'analyse BIA"""
        for record in self:
            record.state = 'approved'
        return True

    def action_draft(self):
        """Remettre en brouillon"""
        for record in self:
            record.state = 'draft'
        return True

    def action_archive(self):
        """Archiver l'analyse"""
        for record in self:
            record.state = 'archived'
        return True

    @api.depends('activity_ids')
    def _compute_activity_count(self):
        for rec in self:
            rec.activity_count = len(rec.activity_ids)

    def action_view_activities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Critical Activities',
            'res_model': 'risk.bia.activity',
            'view_mode': 'list,form',
            'domain': [('bia_id', '=', self.id)],
            'context': {'default_bia_id': self.id}
        }

    @api.depends('impact_operational', 'impact_financial')
    def _compute_priority(self):
        for rec in self:
            op = int(rec.impact_operational or 1)
            fin = int(rec.impact_financial or 1)
            max_impact = max(op, fin)
            rec.priority = str(max_impact)

