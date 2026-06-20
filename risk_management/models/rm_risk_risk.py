from dateutil.relativedelta import relativedelta

from odoo import models, fields, api


class RiskRisk(models.Model):
    _name = 'risk.risk'
    _description = 'Risk'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Risque', required=True, tracking=True)
    code = fields.Char(string='Code', readonly=True, default='New', tracking=True)
    description = fields.Html(string='Description')
    cause_description = fields.Html(string='Cause')
    consequence_description = fields.Html(string='Conséquence')
    category_id = fields.Many2one('risk.category', required=True, tracking=True)
    subcategory_id = fields.Many2one('risk.subcategory', tracking=True)
    owner_id = fields.Many2one('hr.employee', string='Risk Owner', tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    appetite = fields.Selection([
        ('very_low', 'Very Low'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='medium')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated'),
        ('obsolete', 'Obsolete')
    ], default='draft', tracking=True)
    cause_ids = fields.Many2many('risk.cause', string='Causes')
    impact_ids = fields.Many2many('risk.impact', string='Impacts')
    regulation_ids = fields.Many2many('risk.regulation', string='Regulations')
    asset_ids = fields.Many2many('risk.asset', string='Assets')
    organization_ids = fields.Many2many('risk.organization', string='Organization Units')
    active = fields.Boolean(default=True)
    control_ids = fields.Many2many('risk.control', string='Controls')
    kri_ids = fields.Many2many('risk.kri', string='KRIs')
    incident_ids = fields.One2many('risk.incident', 'risk_id')
    incident_count = fields.Integer(compute='_compute_incident_count')
    total_loss_amount = fields.Monetary(compute='_compute_total_loss')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    audit_finding_ids = fields.One2many('risk.audit.finding', 'risk_id')
    audit_finding_count = fields.Integer(compute='_compute_audit_finding_count')
    compliance_requirement_ids = fields.Many2many('risk.compliance.requirement', string='Compliance Requirements')
    inherent_probability = fields.Selection([
        ('1', 'Very Low'),
        ('2', 'Low'),
        ('3', 'Medium'),
        ('4', 'High'),
        ('5', 'Very High')
    ], default='1')
    inherent_impact = fields.Selection([
        ('1', 'Insignificant'),
        ('2', 'Minor'),
        ('3', 'Moderate'),
        ('4', 'Major'),
        ('5', 'Catastrophic')
    ], default='1')
    inherent_score = fields.Integer(compute='_compute_scores', store=True)
    inherent_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], compute='_compute_scores', store=True)
    residual_probability = fields.Selection([
        ('1', 'Very Low'),
        ('2', 'Low'),
        ('3', 'Medium'),
        ('4', 'High'),
        ('5', 'Very High')
    ], default='1')
    residual_impact = fields.Selection([
        ('1', 'Insignificant'),
        ('2', 'Minor'),
        ('3', 'Moderate'),
        ('4', 'Major'),
        ('5', 'Catastrophic')
    ], default='1')
    residual_score = fields.Integer(compute='_compute_scores', store=True)
    residual_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], compute='_compute_scores', store=True)
    review_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semiannual', 'Semi-Annual'),
        ('annual', 'Annual')
    ], default='quarterly', tracking=True)
    last_review_date = fields.Date(tracking=True)
    next_review_date = fields.Date(compute='_compute_next_review_date', store=True, tracking=True)
    review_overdue = fields.Boolean(compute='_compute_review_overdue', store=True)
    risk_type = fields.Selection([
        ('strategic', 'Strategic'),
        ('operational', 'Operational'),
        ('financial', 'Financial'),
        ('compliance', 'Compliance'),
        ('cyber', 'Cybersecurity'),
        ('reputation', 'Reputation'),
        ('liquidity', 'Liquidity'),
        ('market', 'Market')
    ], string='Risk Type', tracking=True)
    risk_source = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
        ('regulatory', 'Regulatory'),
        ('technology', 'Technology'),
        ('human', 'Human'),
        ('supplier', 'Supplier')
    ], string='Risk Source', tracking=True)
    cause = fields.Html(string='Cause')
    risk_event = fields.Html(string='Risk Event')
    consequence = fields.Html(string='Consequence')
    existing_control = fields.Html(string='Existing Controls')
    assessment_ids = fields.One2many('risk.assessment', 'risk_id', string='Assessments')
    activity_id = fields.Many2one('risk.activity', string='Activité', ondelete='set null', tracking=True,
                                  help='Activité concernée par ce risque')
    process_id = fields.Many2one('risk.process', related='activity_id.process_id', store=True, string='Processus')
    risk_level = fields.Selection([
        ('1', 'Très faible'),
        ('2', 'Faible'),
        ('3', 'Moyen'),
        ('4', 'Élevé'),
        ('5', 'Critique')
    ], string='Niveau de risque', default='1', help='Niveau de risque (1 = Très faible, 5 = Critique)')
    macro_process_id = fields.Many2one('risk.macro.process', related='activity_id.macro_process_id', store=True,
                                       string='Macro Processus')
    last_assessment_id = fields.Many2one('risk.assessment', compute='_compute_last_assessment', compute_sudo=True,
                                         store=True, string='Dernière évaluation')
    last_assessment_date = fields.Date(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                       string='Date dernière évaluation')
    last_inherent_score = fields.Integer(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                         string='Score inhérent (dernière éval.)')
    last_residual_score = fields.Integer(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                         string='Score résiduel (dernière éval.)')
    last_risk_level = fields.Selection([
        ('low', 'Faible'),
        ('moderate', 'Modéré'),
        ('important', 'Important'),
        ('high', 'Élevé'),
        ('critical', 'Critique')
    ], compute='_compute_last_assessment', compute_sudo=True, store=True, string='Niveau de risque (dernière éval.)')
    last_over_appetite = fields.Boolean(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                        string='Hors appétit (dernière éval.)')
    last_inherent_probability = fields.Integer(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                               string='Probabilité inhérente (dernière éval.)')
    last_inherent_impact = fields.Integer(compute='_compute_last_assessment', compute_sudo=True, store=True,
                                          string='Impact inhérent (dernière éval.)')
    assessment_count = fields.Integer(compute='_compute_assessment_count', compute_sudo=True, store=True,
                                      string="Nombre d'évaluations")

    # Champs pour la matrice
    impact_value = fields.Integer(compute='_compute_impact_values', store=True, string='Impact Value')
    probability_value = fields.Integer(compute='_compute_impact_values', store=True, string='Probability Value')
    matrix_html = fields.Html(compute='_compute_matrix_html', string='Position du risque', sanitize=False, store=False)

    @api.depends('last_review_date', 'review_frequency')
    def _compute_next_review_date(self):
        for rec in self:
            rec.next_review_date = False
            if not rec.last_review_date:
                continue
            if rec.review_frequency == 'monthly':
                rec.next_review_date = rec.last_review_date + relativedelta(months=1)
            elif rec.review_frequency == 'quarterly':
                rec.next_review_date = rec.last_review_date + relativedelta(months=3)
            elif rec.review_frequency == 'semiannual':
                rec.next_review_date = rec.last_review_date + relativedelta(months=6)
            elif rec.review_frequency == 'annual':
                rec.next_review_date = rec.last_review_date + relativedelta(years=1)

    @api.depends('next_review_date')
    def _compute_review_overdue(self):
        today = fields.Date.today()
        for rec in self:
            rec.review_overdue = bool(rec.next_review_date and rec.next_review_date < today)

    @api.depends('inherent_probability', 'inherent_impact', 'residual_probability', 'residual_impact')
    def _compute_scores(self):
        for rec in self:
            inherent = int(rec.inherent_probability or 1) * int(rec.inherent_impact or 1)
            rec.inherent_score = inherent
            residual = int(rec.residual_probability or 1) * int(rec.residual_impact or 1)
            rec.residual_score = residual
            rec.inherent_level = rec._get_level(inherent)
            rec.residual_level = rec._get_level(residual)

    def _get_level(self, score):
        if score <= 5:
            return 'low'
        if score <= 10:
            return 'medium'
        if score <= 15:
            return 'high'
        return 'critical'

    @api.depends('audit_finding_ids')
    def _compute_audit_finding_count(self):
        for rec in self:
            rec.audit_finding_count = len(rec.audit_finding_ids)

    @api.depends('incident_ids')
    def _compute_incident_count(self):
        for rec in self:
            rec.incident_count = len(rec.incident_ids)

    @api.depends('incident_ids.total_loss')
    def _compute_total_loss(self):
        for rec in self:
            rec.total_loss_amount = sum(rec.incident_ids.mapped('total_loss'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', 'New') == 'New':
                vals['code'] = self.env['ir.sequence'].next_by_code('risk.risk')
        return super().create(vals_list)

    def action_assess(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Évaluation du risque',
            'res_model': 'risk.assessment',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_risk_id': self.id,
            },
        }

    def action_close(self):
        for record in self:
            record.state = 'obsolete'
            record.active = False
        return True

    @api.onchange('activity_id')
    def _onchange_activity_id(self):
        if self.activity_id:
            self.process_id = self.activity_id.process_id
            self.macro_process_id = self.activity_id.macro_process_id

    # ============================================================
    # MÉTHODE POUR LA MATRICE
    # ============================================================

    def get_matrix_color(self, score):
        if score <= 4:
            return 'bg-success'
        elif score <= 9:
            return 'bg-warning'
        elif score <= 16:
            return 'bg-orange'
        else:
            return 'bg-danger'

    def get_risk_distribution(self):
        levels = {
            'low': 0,
            'moderate': 0,
            'important': 0,
            'high': 0,
            'critical': 0
        }
        for risk in self.search([('active', '=', True)]):
            level = risk.last_risk_level or 'low'
            if level in levels:
                levels[level] += 1
        return levels

    # ============================================================
    # _compute_last_assessment - UNE SEULE FOIS
    # ============================================================

    @api.depends('assessment_ids', 'assessment_ids.assessment_date')
    def _compute_last_assessment(self):
        for risk in self:
            last = risk.assessment_ids.sorted(
                key=lambda r: r.assessment_date or r.create_date,
                reverse=True
            )[:1]
            if last:
                risk.last_assessment_id = last.id
                risk.last_assessment_date = last.assessment_date
                risk.last_inherent_score = last.inherent_score
                risk.last_residual_score = last.residual_score
                risk.last_risk_level = last.risk_level
                risk.last_over_appetite = last.over_appetite
                risk.last_inherent_probability = last.inherent_probability
                risk.last_inherent_impact = last.inherent_impact
            else:
                risk.last_assessment_id = False
                risk.last_assessment_date = False
                risk.last_inherent_score = 0
                risk.last_residual_score = 0
                risk.last_risk_level = False
                risk.last_over_appetite = False
                risk.last_inherent_probability = 0
                risk.last_inherent_impact = 0

    @api.depends('assessment_ids')
    def _compute_assessment_count(self):
        for risk in self:
            risk.assessment_count = len(risk.assessment_ids)

    @api.depends('inherent_impact', 'inherent_probability')
    def _compute_impact_values(self):
        impact_map = {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            'insignificant': 1, 'minor': 2, 'moderate': 3, 'major': 4, 'catastrophic': 5
        }
        prob_map = {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            'very_low': 1, 'low': 2, 'medium': 3, 'high': 4, 'very_high': 5
        }
        for record in self:
            record.impact_value = impact_map.get(record.inherent_impact, 1)
            record.probability_value = prob_map.get(record.inherent_probability, 1)

    @api.depends(
        'inherent_impact',
        'inherent_probability',
        'inherent_score',
        'inherent_level',
        'residual_impact',
        'residual_probability',
        'residual_score',
        'residual_level'
    )
    def _compute_matrix_html(self):
        for record in self:
            try:
                impact = int(record.inherent_impact or 1)
                probability = int(record.inherent_probability or 1)
                score = record.inherent_score or 0
                level = record.inherent_level or 'non défini'
                residual_score = record.residual_score or 0
                residual_level = record.residual_level or 'non défini'

                html = f'''
                <div class="risk-matrix-wrapper" style="width:100%;max-width:750px;margin:0 auto;padding:20px;background:#fff;border-radius:12px;box-shadow:0 2px 8px rgba(0,0,0,0.1);">
                    <h3 style="text-align:center;font-size:22px;font-weight:700;color:#1a237e;margin-bottom:20px;padding-bottom:12px;border-bottom:3px solid #e8eaf6;">📊 Position du risque</h3>

                    <table style="width:100%;border-collapse:collapse;margin:10px 0;border:1px solid #dee2e6;">
                        <thead>
                            <tr>
                                <th style="background:#f5f5f5;font-weight:700;color:#37474f;border:1px solid #dee2e6;padding:12px 16px;text-align:center;min-width:80px;">Probabilité ↓</th>
                '''

                for i in range(1, 6):
                    html += f'<th style="background:#f5f5f5;font-weight:700;color:#37474f;border:1px solid #dee2e6;padding:12px 16px;text-align:center;min-width:50px;">{i}</th>'
                html += '''
                            </tr>
                        </thead>
                        <tbody>
                '''

                for prob in range(5, 0, -1):
                    html += f'<tr><td style="background:#f5f5f5;font-weight:700;color:#37474f;border:1px solid #dee2e6;padding:12px 16px;text-align:center;min-width:80px;">{prob}</td>'
                    for imp in range(1, 6):
                        score_cell = prob * imp
                        color = record._get_matrix_color(score_cell)
                        is_active = (prob == probability and imp == impact)
                        text_color = 'white' if score_cell > 12 else 'black'
                        active_style = 'border:4px solid #1a237e !important;box-shadow:0 0 0 3px #1a237e;background-color:#ffffff;font-weight:800;transform:scale(1.05);' if is_active else ''
                        html += f'<td style="background-color:{color};color:{text_color};border:1px solid #dee2e6;padding:14px 18px;text-align:center;font-weight:{"800" if is_active else "600"};font-size:16px;cursor:default;transition:all 0.2s ease;{active_style}">{score_cell}</td>'
                    html += '</tr>'

                html += f'''
                        </tbody>
                    </table>

                    <div style="display:flex;justify-content:center;gap:20px;margin:15px 0;flex-wrap:wrap;padding:12px 20px;background:#f8f9fa;border-radius:8px;">
                        <span style="display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#37474f;">
                            <span style="display:inline-block;width:20px;height:20px;border-radius:4px;background:#28a745;border:1px solid #dee2e6;"></span> Faible (1-4)
                        </span>
                        <span style="display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#37474f;">
                            <span style="display:inline-block;width:20px;height:20px;border-radius:4px;background:#ffc107;border:1px solid #dee2e6;"></span> Moyen (5-9)
                        </span>
                        <span style="display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#37474f;">
                            <span style="display:inline-block;width:20px;height:20px;border-radius:4px;background:#fd7e14;border:1px solid #dee2e6;"></span> Élevé (10-16)
                        </span>
                        <span style="display:flex;align-items:center;gap:6px;font-size:13px;font-weight:500;color:#37474f;">
                            <span style="display:inline-block;width:20px;height:20px;border-radius:4px;background:#dc3545;border:1px solid #dee2e6;"></span> Critique (17-25)
                        </span>
                    </div>

                    <div style="text-align:center;margin-top:15px;padding:14px;background:#f8f9fa;border-radius:8px;font-size:15px;">
                        <div style="display:flex;justify-content:center;gap:30px;flex-wrap:wrap;">
                            <div>
                                <strong>Score inhérent :</strong>
                                <span style="font-size:20px;font-weight:700;color:#1a237e;">{score}</span>
                                &nbsp;|&nbsp;
                                <strong>Niveau :</strong>
                                <span class="badge-{level.lower() if level else 'non-defini'}">{level.capitalize() if level else 'Non défini'}</span>
                            </div>
                            <div>
                                <strong>Score résiduel :</strong>
                                <span style="font-size:20px;font-weight:700;color:#1a237e;">{residual_score}</span>
                                &nbsp;|&nbsp;
                                <strong>Niveau :</strong>
                                <span class="badge-{residual_level.lower() if residual_level else 'non-defini'}">{residual_level.capitalize() if residual_level else 'Non défini'}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <style>
                    .badge-low {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#d4edda;color:#155724; }}
                    .badge-medium {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#fff3cd;color:#856404; }}
                    .badge-high {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#ffe5cc;color:#853d04; }}
                    .badge-critical {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#f8d7da;color:#721c24; }}
                    .badge-non-defini {{ display:inline-block;padding:4px 14px;border-radius:20px;font-weight:600;font-size:14px;background:#e2e3e5;color:#383d41; }}
                </style>
                '''

                record.matrix_html = html

            except Exception as e:
                record.matrix_html = f'<div style="color:red;padding:20px;text-align:center;background:#fff5f5;border-radius:8px;">❌ Erreur: {str(e)}</div>'

    def _get_matrix_color(self, score):
        if score <= 4:
            return '#28a745'
        elif score <= 9:
            return '#ffc107'
        elif score <= 16:
            return '#fd7e14'
        else:
            return '#dc3545'

    # Dans rm_risk_risk.py
    graph_impact = fields.Integer(
        compute='_compute_graph_values',
        store=False,
        string='Impact (graphique)'
    )

    graph_probability = fields.Integer(
        compute='_compute_graph_values',
        store=False,
        string='Probabilité (graphique)'
    )

    @api.depends('inherent_impact', 'inherent_probability')
    def _compute_graph_values(self):
        mapping = {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            'insignificant': 1, 'minor': 2, 'moderate': 3, 'major': 4, 'catastrophic': 5
        }
        for record in self:
            record.graph_impact = mapping.get(record.inherent_impact, 1)
            record.graph_probability = mapping.get(record.inherent_probability, 1)

    # ============================================================
    # MÉTHODES POUR LE TABLEAU DE BORD
    # ============================================================

    def get_dashboard_stats(self):
        """Retourne les statistiques pour le dashboard"""
        stats = {
            'total': 0,
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'total_score': 0,
            'avg_score': 0,
            'total_incidents': 0,
            'total_loss': 0
        }

        risks = self.search([('active', '=', True)])
        stats['total'] = len(risks)

        for risk in risks:
            stats['total_score'] += risk.inherent_score or 0
            if risk.inherent_level == 'critical':
                stats['critical'] += 1
            elif risk.inherent_level == 'high':
                stats['high'] += 1
            elif risk.inherent_level == 'medium':
                stats['medium'] += 1
            elif risk.inherent_level == 'low':
                stats['low'] += 1
            stats['total_incidents'] += risk.incident_count or 0
            stats['total_loss'] += risk.total_loss_amount or 0

        stats['avg_score'] = round(stats['total_score'] / stats['total'], 2) if stats['total'] > 0 else 0

        return stats

    def get_matrix_data(self):
        """Retourne les données pour la matrice 5x5"""
        matrix = {}
        for i in range(1, 6):
            for j in range(1, 6):
                matrix[f"{i}_{j}"] = 0

        risks = self.search([('active', '=', True)])
        for risk in risks:
            impact = int(risk.inherent_impact or 1)
            prob = int(risk.inherent_probability or 1)
            key = f"{prob}_{impact}"
            if key in matrix:
                matrix[key] += 1

        return matrix

    @api.depends('inherent_impact', 'inherent_probability')
    def _compute_pivot_values(self):
        mapping = {
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
            'insignificant': 1, 'minor': 2, 'moderate': 3, 'major': 4, 'catastrophic': 5
        }
        for record in self:
            record.impact_value = mapping.get(record.inherent_impact, 1)
            record.probability_value = mapping.get(record.inherent_probability, 1)