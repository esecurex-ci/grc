import base64
import csv
import io

from odoo import models, fields, api
from odoo.exceptions import ValidationError

LEVEL_RANK = {'low': 1, 'medium': 2, 'high': 3}
LEVEL_LABELS = {'low': 'Faible', 'medium': 'Modéré', 'high': 'Élevé'}


class RiskAssessmentPeriod(models.Model):
    _name = 'risk.assessment.period'
    _description = 'Evaluation périodique des risques'
    _order = 'date_start desc'

    name = fields.Char(
        required=True,
        string='Désignation',
    )

    code = fields.Char(string='Code')

    date_start = fields.Date(
        required=True,
        string='Date de début'
    )

    date_end = fields.Date(
        required=True,
        string='Date clôture'
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('open', 'Ouvert'),
            ('closed', 'Clôturé')
        ],
        default='draft',
        tracking=True,
        string='Status'
    )

    active = fields.Boolean(
        default=True
    )

    assessment_ids = fields.One2many(
        'risk.assessment',
        'period_id',
        string='Evaluations',
    )

    assessment_count = fields.Integer(
        compute='_compute_assessment_count',
        string='Evaluations',
    )

    only_my_risks = fields.Boolean(
        string='Filtrer sur mes risques',
        help="Limite le tableau ci-dessous aux risques rattachés au(x) "
             "macro-processus dont l'utilisateur connecté est responsable "
             "(risk.macro.process.owner_id), au lieu de tout le registre."
    )

    campaign_risk_ids = fields.Many2many(
        'risk.risk',
        compute='_compute_campaign_risk_ids',
        string='Risques de la campagne',
        help="Tous les risques actifs du registre (évalués ou non sur cette "
             "période), ou seulement ceux du périmètre de l'utilisateur "
             "connecté si 'only_my_risks' est coché."
    )

    total_risk_count = fields.Integer(
        compute='_compute_register_stats',
        string='Nombre de risques'
    )

    high_risk_count = fields.Integer(
        compute='_compute_register_stats',
        string='Risques élevés'
    )

    pending_risk_count = fields.Integer(
        compute='_compute_register_stats',
        string='Restant à évaluer',
        help="Risques actifs du registre qui n'ont pas encore d'évaluation sur cette période."
    )

    @api.depends('assessment_ids')
    def _compute_assessment_count(self):
        for rec in self:
            rec.assessment_count = len(rec.assessment_ids)

    @api.depends('only_my_risks')
    def _compute_campaign_risk_ids(self):
        employee = self.env.user.employee_id
        all_risks = self.env['risk.risk'].search([('active', '=', True)])
        for rec in self:
            if rec.only_my_risks and employee:
                rec.campaign_risk_ids = all_risks.filtered(
                    lambda r: r.macro_process_id.owner_id.id == employee.id
                )
            else:
                rec.campaign_risk_ids = all_risks

    @api.depends('assessment_ids')
    def _compute_register_stats(self):
        all_risks = self.env['risk.risk'].search([('active', '=', True)])
        high_count = len(all_risks.filtered(lambda r: r.inherent_level == 'high'))
        for rec in self:
            rec.total_risk_count = len(all_risks)
            rec.high_risk_count = high_count
            rec.pending_risk_count = max(0, len(all_risks) - len(rec.assessment_ids))

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for rec in self:
            if rec.date_end < rec.date_start:
                raise ValidationError(
                    "La date de clôture doit être supérieure à la date de début."
                )

    ##################################################################
    # WORKFLOW & EXPORT
    ##################################################################

    def action_close(self):
        self.write({'state': 'closed'})

    def action_export(self):
        """Exporte en CSV le tableau de la campagne : chaque risque actif du
        registre avec son évaluation sur CETTE période (si elle existe)."""
        self.ensure_one()

        risks = self.env['risk.risk'].search([('active', '=', True)])

        buffer = io.StringIO()
        writer = csv.writer(buffer, delimiter=';')
        writer.writerow([
            'Code', 'Risque', 'Niveau inhérent', 'Niveau résiduel',
            'Écart', 'Évaluateur', 'Statut',
        ])

        for risk in risks:
            assessment = self.env['risk.assessment'].search([
                ('risk_id', '=', risk.id),
                ('period_id', '=', self.id),
            ], limit=1)

            residual_label = ''
            assessor_name = ''
            gap_label = ''
            state_label = 'Non évalué'

            if assessment:
                residual_label = LEVEL_LABELS.get(assessment.risk_level, '')
                assessor_name = assessment.assessor_id.name or ''
                state_label = dict(
                    assessment._fields['state'].selection
                ).get(assessment.state, '')

                inherent_rank = LEVEL_RANK.get(risk.inherent_level, 0)
                residual_rank = LEVEL_RANK.get(assessment.risk_level, 0)
                if inherent_rank and residual_rank:
                    gap_label = f"{residual_rank - inherent_rank:+d}"

            writer.writerow([
                risk.code or '',
                risk.name or '',
                LEVEL_LABELS.get(risk.inherent_level, ''),
                residual_label,
                gap_label,
                assessor_name,
                state_label,
            ])

        attachment = self.env['ir.attachment'].create({
            'name': f"Campagne_{self.code or self.name}.csv",
            'type': 'binary',
            'datas': base64.b64encode(buffer.getvalue().encode('utf-8-sig')),
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }