import base64
import io

import xlsxwriter

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
             "processus dont l'utilisateur connecté est responsable "
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

    progress_percent = fields.Float(
        compute='_compute_register_stats',
        string='Progression de la campagne',
        help="Pourcentage de risques du registre déjà évalués sur cette période."
    )

    pending_risk_count = fields.Integer(
        compute='_compute_register_stats',
        string='Restant à évaluer',
        help="La cartographie ne comporte pas de notion de risque hors "
             "appétit : ce KPI indique simplement combien de risques du "
             "registre n'ont pas encore été évalués sur cette période."
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
        total = len(all_risks)
        high_count = len(all_risks.filtered(lambda r: r.inherent_level == 'high'))
        for rec in self:
            rec.total_risk_count = total
            rec.high_risk_count = high_count
            rec.progress_percent = (len(rec.assessment_ids) / total * 100) if total else 0.0
            rec.pending_risk_count = max(0, total - len(rec.assessment_ids))

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
        """Exporte en XLSX (mise en forme, couleurs par niveau) le tableau de
        la campagne : chaque risque actif du registre avec son évaluation sur
        CETTE période (si elle existe)."""
        self.ensure_one()

        risks = self.env['risk.risk'].search([('active', '=', True)])

        buffer = io.BytesIO()
        workbook = xlsxwriter.Workbook(buffer, {'in_memory': True})
        sheet = workbook.add_worksheet('Campagne')

        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#1a237e',
            'font_color': '#ffffff',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })
        base_format = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        center_format = workbook.add_format({'border': 1, 'valign': 'vcenter', 'align': 'center'})

        level_formats = {
            'low': workbook.add_format({
                'border': 1, 'valign': 'vcenter', 'align': 'center',
                'bg_color': '#d4edda', 'font_color': '#155724',
            }),
            'medium': workbook.add_format({
                'border': 1, 'valign': 'vcenter', 'align': 'center',
                'bg_color': '#fff3cd', 'font_color': '#856404',
            }),
            'high': workbook.add_format({
                'border': 1, 'valign': 'vcenter', 'align': 'center',
                'bg_color': '#f8d7da', 'font_color': '#721c24',
            }),
            False: center_format,
        }

        headers = [
            'Code', 'Risque', 'Niveau inhérent', 'Niveau résiduel',
            'Écart', 'Écart vs éval. précédente', 'Évaluateur', 'Statut',
        ]
        for col, title in enumerate(headers):
            sheet.write(0, col, title, header_format)

        row = 1
        for risk in risks:
            assessment = self.env['risk.assessment'].search([
                ('risk_id', '=', risk.id),
                ('period_id', '=', self.id),
            ], limit=1)

            residual_level_key = False
            residual_label = ''
            assessor_name = ''
            gap_label = ''
            variation_label = ''
            state_label = 'Non évalué'

            if assessment:
                residual_level_key = assessment.risk_level
                residual_label = LEVEL_LABELS.get(assessment.risk_level, '')
                assessor_name = assessment.assessor_id.name or ''
                state_label = dict(
                    assessment._fields['state'].selection
                ).get(assessment.state, '')

                inherent_rank = LEVEL_RANK.get(risk.inherent_level, 0)
                residual_rank = LEVEL_RANK.get(assessment.risk_level, 0)
                if inherent_rank and residual_rank:
                    gap_label = f"{residual_rank - inherent_rank:+d}"

                # Variation vs la campagne antérieure la plus récente pour ce
                # même risque (même logique que assessment_residual_variation_for_period
                # sur risk.risk, exclusion de l'évaluation de cette période).
                previous_assessment = self.env['risk.assessment'].search([
                    ('risk_id', '=', risk.id),
                    ('period_id', '!=', self.id),
                ], order='assessment_date desc', limit=1)

                if previous_assessment:
                    previous_rank = LEVEL_RANK.get(previous_assessment.risk_level, 0)
                    if previous_rank and residual_rank:
                        previous_label = LEVEL_LABELS.get(previous_assessment.risk_level, '')
                        current_label = LEVEL_LABELS.get(assessment.risk_level, '')
                        gap = residual_rank - previous_rank
                        if gap == 0:
                            variation_label = f"Stable ({current_label})"
                        else:
                            n = abs(gap)
                            unit = 'niveau' if n == 1 else 'niveaux'
                            direction = 'Dégradé' if gap > 0 else 'Amélioré'
                            variation_label = (
                                f"{direction} : {previous_label} → {current_label} "
                                f"({n} {unit})"
                            )

            sheet.write(row, 0, risk.code or '', base_format)
            sheet.write(row, 1, risk.name or '', base_format)
            sheet.write(row, 2, LEVEL_LABELS.get(risk.inherent_level, ''), level_formats.get(risk.inherent_level, center_format))
            sheet.write(row, 3, residual_label, level_formats.get(residual_level_key, center_format))
            sheet.write(row, 4, gap_label, center_format)
            sheet.write(row, 5, variation_label, center_format)
            sheet.write(row, 6, assessor_name, base_format)
            sheet.write(row, 7, state_label, base_format)
            row += 1

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 45)
        sheet.set_column(2, 3, 16)
        sheet.set_column(4, 4, 10)
        sheet.set_column(5, 5, 34)
        sheet.set_column(6, 6, 22)
        sheet.set_column(7, 7, 16)
        sheet.freeze_panes(1, 0)
        sheet.autofilter(0, 0, row - 1, len(headers) - 1)

        workbook.close()
        buffer.seek(0)

        attachment = self.env['ir.attachment'].create({
            'name': f"Campagne_{self.code or self.name}.xlsx",
            'type': 'binary',
            'datas': base64.b64encode(buffer.getvalue()),
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }