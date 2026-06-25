from odoo import models, fields

class RiskKriAlert(models.Model):
    _name = 'risk.kri.alert'
    _description = 'KRI Alert'
    _order = 'create_date desc'

    kri_id = fields.Many2one('risk.kri', string='KRI', required=True, ondelete='cascade')
    status = fields.Selection([
        ('amber', 'Amber'),
        ('red', 'Red'),
    ], string='Niveau d\'alerte', required=True)
    value = fields.Float(string='Valeur', required=True)
    threshold = fields.Float(string='Seuil déclencheur', required=True)
    message = fields.Text(string='Message')
    acknowledged = fields.Boolean(string='Accusé de réception', default=False)
    acknowledged_date = fields.Datetime(string="Date d'accusé de réception")
    acknowledged_by = fields.Many2one('res.users', string="Accusé par")
    resolved = fields.Boolean(string='Résolu', default=False)
    resolved_date = fields.Datetime(string='Date de résolution')
    resolved_by = fields.Many2one('res.users', string='Résolu par')
    action_taken = fields.Html(string='Action entreprise')

    def action_acknowledge(self):
        """Accuse réception de l'alerte"""
        self.ensure_one()
        self.write({
            'acknowledged': True,
            'acknowledged_date': fields.Datetime.now(),
            'acknowledged_by': self.env.user.id,
        })

    def action_resolve(self):
        """Marque l'alerte comme résolue"""
        self.ensure_one()
        self.write({
            'resolved': True,
            'resolved_date': fields.Datetime.now(),
            'resolved_by': self.env.user.id,
        })