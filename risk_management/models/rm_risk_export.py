# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import io
import json
import csv
import xlsxwriter
from datetime import datetime


class RiskExportWizard(models.TransientModel):
    _name = 'risk.export.wizard'
    _description = "Assistant d'export des données GRC"

    # Options d'export
    export_type = fields.Selection([
        ('risks', 'Risques uniquement'),
        ('risks_with_relations', 'Risques avec relations'),
        ('full', 'Données complètes'),
        ('matrix', 'Matrice des risques'),
    ], string="Type d'export", default='risks', required=True)

    export_format = fields.Selection([
        ('xlsx', 'Excel (.xlsx)'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('xml', 'XML'),
    ], string="Format d'export", default='xlsx', required=True)

    include_relations = fields.Boolean(string="Inclure les relations", default=True)
    include_historical = fields.Boolean(string="Inclure l'historique", default=False)

    file_name = fields.Char(string='Nom du fichier')
    file_data = fields.Binary(string='Fichier', attachment=True)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('done', 'Terminé'),
    ], string='Statut', default='draft')

    # Statistiques
    total_risks = fields.Integer(compute='_compute_stats', string='Total risques')
    total_controls = fields.Integer(compute='_compute_stats', string='Total contrôles')
    total_incidents = fields.Integer(compute='_compute_stats', string='Total incidents')
    total_kris = fields.Integer(compute='_compute_stats', string='Total KRI')

    @api.depends()
    def _compute_stats(self):
        """Calcule les statistiques pour l'aperçu"""
        for record in self:
            risks = self.env['risk.risk'].search([('active', '=', True)])
            record.total_risks = len(risks)
            record.total_controls = len(risks.mapped('control_ids'))
            record.total_incidents = len(risks.mapped('incident_ids'))
            record.total_kris = len(risks.mapped('kri_ids'))

    def action_export(self):
        """Exécute l'export selon les options"""
        self.ensure_one()

        if self.export_format == 'xlsx':
            return self._export_xlsx()
        elif self.export_format == 'csv':
            return self._export_csv()
        elif self.export_format == 'json':
            return self._export_json()
        elif self.export_format == 'xml':
            return self._export_xml()

        raise UserError("Format d'export non supporté.")

    def _get_risks(self):
        """Récupère les risques à exporter"""
        return self.env['risk.risk'].search([('active', '=', True)])

    def _get_level_color(self, level):
        """Retourne la couleur selon le niveau de risque"""
        colors = {
            'critical': '#dc3545',
            'high': '#fd7e14',
            'medium': '#ffc107',
            'low': '#28a745',
        }
        return colors.get(level, '#6c757d')

    def _get_level_bg_color(self, level):
        """Retourne la couleur de fond selon le niveau de risque"""
        colors = {
            'critical': '#f8d7da',
            'high': '#ffe5cc',
            'medium': '#fff3cd',
            'low': '#d4edda',
        }
        return colors.get(level, '#f8f9fa')

    def _get_control_level_label(self, level):
        """Retourne le libellé du niveau de contrôle"""
        labels = {
            'ineffective': 'Inefficace ou informel',
            'partially_effective': 'Partiellement efficace',
            'effective': 'Efficace',
        }
        return labels.get(level, level or 'Non défini')

    def _export_xlsx(self):
        """Export Excel complet avec couleurs et dates formatées"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Formats de base
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#1a237e', 'font_color': 'white',
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        cell_format = workbook.add_format({
            'align': 'left', 'valign': 'vcenter', 'border': 1, 'text_wrap': True
        })
        number_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1
        })
        date_format = workbook.add_format({
            'align': 'center', 'valign': 'vcenter', 'border': 1,
            'num_format': 'dd/mm/yyyy'
        })

        risks = self._get_risks()

        if self.export_type == 'matrix':
            worksheet = workbook.add_worksheet('Matrice')
            self._write_matrix_sheet(worksheet, workbook, risks, header_format, cell_format, number_format)
        else:
            # Feuille principale : Risques
            worksheet = workbook.add_worksheet('Risques')
            self._write_risks_sheet(worksheet, workbook, risks, header_format, cell_format, number_format, date_format)

            # Feuilles supplémentaires
            if self.export_type in ['risks_with_relations', 'full']:
                self._write_controls_sheet(workbook, risks, header_format, cell_format, number_format)
                self._write_incidents_sheet(workbook, risks, header_format, cell_format, number_format, date_format)
                self._write_kris_sheet(workbook, risks, header_format, cell_format, number_format)

            if self.export_type == 'full':
                self._write_actions_sheet(workbook, risks, header_format, cell_format, number_format, date_format)

        # Synthèse
        self._write_summary_sheet(workbook, risks, header_format, cell_format, number_format)

        workbook.close()
        output.seek(0)

        file_data = base64.b64encode(output.getvalue())
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"export_grc_{timestamp}.xlsx"

        self.write({
            'file_name': filename,
            'file_data': file_data,
            'state': 'done'
        })

        return self._open_result()

    def _write_risks_sheet(self, worksheet, workbook, risks, header_format, cell_format, number_format, date_format):
        """Écrit la feuille des risques avec couleurs et processus"""
        headers = [
            'Code', 'Nom du risque', 'Catégorie', 'Sous-catégorie',
            'Type', 'Source', 'Statut', 'Propriétaire',
            # Hiérarchie
            'Processus', 'Sous Processus', 'Activité',
            # Évaluation inhérente
            'Probabilité inhérente', 'Impact inhérent',
            'Score inhérent', 'Niveau inhérent',
            # Évaluation des contrôles
            "Niveau d'efficacité des contrôles",
            # Évaluation résiduelle
            'Score résiduel', 'Niveau résiduel',
            # Dates
            'Dernière révision', 'Prochaine révision',
            'Actif'
        ]

        # Largeur des colonnes
        col_widths = [12, 30, 18, 18, 15, 15, 12, 18, 18, 18, 18, 18, 15, 12, 15, 22, 12, 15, 18, 18, 15, 10]
        for col, width in enumerate(col_widths):
            worksheet.set_column(col, col, width)

        # En-têtes
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        row = 1
        for risk in risks:
            col = 0

            # Code
            worksheet.write(row, col, risk.code or '', cell_format)
            col += 1

            # Nom
            worksheet.write(row, col, risk.name or '', cell_format)
            col += 1

            # Catégorie
            worksheet.write(row, col, risk.category_id.name or '', cell_format)
            col += 1

            # Sous-catégorie
            worksheet.write(row, col, risk.subcategory_id.name or '', cell_format)
            col += 1

            # Type
            worksheet.write(row, col, self._get_selection_label('risk_type', risk.risk_type), cell_format)
            col += 1

            # Source
            worksheet.write(row, col, self._get_selection_label('risk_source', risk.risk_source), cell_format)
            col += 1

            # Statut
            worksheet.write(row, col, self._get_selection_label('state', risk.state), cell_format)
            col += 1

            # Propriétaire
            worksheet.write(row, col, risk.owner_id.name or '', cell_format)
            col += 1

            # Macro-processus
            worksheet.write(row, col, risk.macro_process_id.name or '', cell_format)
            col += 1

            # Processus
            worksheet.write(row, col, risk.process_id.name or '', cell_format)
            col += 1

            # Activité
            worksheet.write(row, col, risk.activity_id.name or '', cell_format)
            col += 1

            # Probabilité inhérente
            worksheet.write(row, col, risk.inherent_probability or '', number_format)
            col += 1

            # Impact inhérent
            worksheet.write(row, col, risk.inherent_impact or '', number_format)
            col += 1

            # Score inhérent avec couleur
            score = risk.inherent_score or 0
            level = risk.inherent_level or 'low'
            score_format = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bold': True,
                'bg_color': self._get_level_bg_color(level),
                'font_color': self._get_level_color(level)
            })
            worksheet.write(row, col, score, score_format)
            col += 1

            # Niveau inhérent avec couleur
            level_format = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bold': True,
                'bg_color': self._get_level_bg_color(level),
                'font_color': self._get_level_color(level)
            })
            # Utiliser la méthode corrigée pour obtenir le libellé
            level_label = self._get_selection_label('inherent_level', level)
            worksheet.write(row, col, level_label, level_format)
            col += 1

            # Niveau d'efficacité des contrôles
            control_level = risk.control_effectiveness_level or 'ineffective'
            control_label = self._get_control_level_label(control_level)
            control_colors = {
                'ineffective': '#f8d7da',
                'partially_effective': '#fff3cd',
                'effective': '#d4edda',
            }
            control_text_colors = {
                'ineffective': '#721c24',
                'partially_effective': '#856404',
                'effective': '#155724',
            }
            control_format = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bold': True,
                'bg_color': control_colors.get(control_level, '#f8f9fa'),
                'font_color': control_text_colors.get(control_level, '#000000')
            })
            worksheet.write(row, col, control_label, control_format)
            col += 1

            # Score résiduel avec couleur
            residual_score = risk.residual_score or 0
            residual_level = risk.residual_level or 'low'
            residual_score_format = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bold': True,
                'bg_color': self._get_level_bg_color(residual_level),
                'font_color': self._get_level_color(residual_level)
            })
            worksheet.write(row, col, residual_score, residual_score_format)
            col += 1

            # Niveau résiduel avec couleur
            residual_level_format = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bold': True,
                'bg_color': self._get_level_bg_color(residual_level),
                'font_color': self._get_level_color(residual_level)
            })
            residual_label = self._get_selection_label('residual_level', residual_level)
            worksheet.write(row, col, residual_label, residual_level_format)
            col += 1

            # Dates
            if risk.last_review_date:
                if isinstance(risk.last_review_date, datetime):
                    worksheet.write_datetime(row, col, risk.last_review_date, date_format)
                else:
                    worksheet.write(row, col,
                                    risk.last_review_date.strftime('%d/%m/%Y') if risk.last_review_date else '',
                                    cell_format)
            else:
                worksheet.write(row, col, '', cell_format)
            col += 1

            if risk.next_review_date:
                if isinstance(risk.next_review_date, datetime):
                    worksheet.write_datetime(row, col, risk.next_review_date, date_format)
                else:
                    worksheet.write(row, col,
                                    risk.next_review_date.strftime('%d/%m/%Y') if risk.next_review_date else '',
                                    cell_format)
            else:
                worksheet.write(row, col, '', cell_format)
            col += 1

            # Actif
            worksheet.write(row, col, 'Oui' if risk.active else 'Non', cell_format)

            row += 1

    def _write_matrix_sheet(self, worksheet, workbook, risks, header_format, cell_format, number_format):
        """Écrit la feuille de la matrice 5x5 avec couleurs"""
        worksheet.write(0, 0, 'Probabilité ↓ / Impact →', header_format)
        for i in range(1, 6):
            worksheet.write(0, i, str(i), header_format)
        worksheet.write(0, 6, 'Total', header_format)

        matrix = {}
        for i in range(1, 6):
            for j in range(1, 6):
                matrix[f"{i}_{j}"] = 0

        for risk in risks:
            prob = int(risk.inherent_probability or 1)
            impact = int(risk.inherent_impact or 1)
            key = f"{prob}_{impact}"
            if key in matrix:
                matrix[key] += 1

        row = 1
        for prob in range(5, 0, -1):
            worksheet.write(row, 0, str(prob), cell_format)
            total_row = 0
            for impact in range(1, 6):
                key = f"{prob}_{impact}"
                count = matrix.get(key, 0)
                total_row += count
                score = prob * impact
                color = self._get_matrix_color(score)
                cell_format_color = workbook.add_format({
                    'align': 'center', 'valign': 'vcenter', 'border': 1,
                    'bg_color': color, 'font_color': 'white' if score > 12 else 'black',
                    'bold': True
                })
                worksheet.write(row, impact, count, cell_format_color)
            worksheet.write(row, 6, total_row, number_format)
            row += 1

        worksheet.write(row, 0, 'Total', header_format)
        for impact in range(1, 6):
            total_col = sum(matrix.get(f"{prob}_{impact}", 0) for prob in range(1, 6))
            worksheet.write(row, impact, total_col, number_format)
        worksheet.write(row, 6, len(risks), number_format)

        # Légende
        worksheet.write(row + 2, 0, 'Légende :', header_format)
        legend_colors = [
            ('Faible (1-5)', '#28a745'),
            ('Modéré (6-15)', '#ffc107'),
            ('Élevé (16-25)', '#fd7e14'),
        ]
        for i, (label, color) in enumerate(legend_colors):
            cell_format_color = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': color, 'font_color': 'white' if i > 1 else 'black',
                'bold': True
            })
            worksheet.write(row + 2 + i, 1, label, cell_format_color)

        worksheet.set_column(0, 0, 25)
        for i in range(1, 7):
            worksheet.set_column(i, i, 12)

    def _write_controls_sheet(self, workbook, risks, header_format, cell_format, number_format):
        """Écrit la feuille des contrôles"""
        worksheet = workbook.add_worksheet('Contrôles')
        headers = ['Code risque', 'Risque', 'Contrôle', 'Type', 'Efficacité', 'Statut']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 18)

        effectiveness_formats = {
            'high': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#d4edda', 'font_color': '#155724',
                 'bold': True}),
            'medium': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#fff3cd', 'font_color': '#856404',
                 'bold': True}),
            'low': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#f8d7da', 'font_color': '#721c24',
                 'bold': True}),
        }

        row = 1
        for risk in risks:
            for control in risk.control_ids:
                worksheet.write(row, 0, risk.code or '', cell_format)
                worksheet.write(row, 1, risk.name or '', cell_format)
                worksheet.write(row, 2, control.name or '', cell_format)
                worksheet.write(row, 3, self._get_selection_label('control_type', control.control_type), cell_format)
                eff = control.effectiveness or ''
                eff_label = self._get_effectiveness_label(eff)
                eff_format = effectiveness_formats.get(eff, cell_format)
                worksheet.write(row, 4, eff_label, eff_format)
                worksheet.write(row, 5, self._get_selection_label('state', control.state), cell_format)
                row += 1

    def _write_incidents_sheet(self, workbook, risks, header_format, cell_format, number_format, date_format):
        """Écrit la feuille des incidents avec dates formatées"""
        worksheet = workbook.add_worksheet('Incidents')
        headers = ['Code risque', 'Risque', 'Incident', 'Date', 'Gravité', 'Perte (FCFA)']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 18)

        severity_formats = {
            'critical': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#f8d7da', 'font_color': '#721c24',
                 'bold': True}),
            'high': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#ffe5cc', 'font_color': '#853d04',
                 'bold': True}),
            'medium': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#fff3cd', 'font_color': '#856404',
                 'bold': True}),
            'low': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#d4edda', 'font_color': '#155724',
                 'bold': True}),
        }

        row = 1
        for risk in risks:
            for incident in risk.incident_ids:
                worksheet.write(row, 0, risk.code or '', cell_format)
                worksheet.write(row, 1, risk.name or '', cell_format)
                worksheet.write(row, 2, incident.name or '', cell_format)
                if incident.incident_date:
                    if isinstance(incident.incident_date, datetime):
                        worksheet.write_datetime(row, 3, incident.incident_date, date_format)
                    else:
                        worksheet.write(row, 3,
                                        incident.incident_date.strftime('%d/%m/%Y') if incident.incident_date else '',
                                        cell_format)
                else:
                    worksheet.write(row, 3, '', cell_format)
                severity = incident.severity or ''
                severity_label = self._get_selection_label('severity', severity)
                severity_format = severity_formats.get(severity, cell_format)
                worksheet.write(row, 4, severity_label, severity_format)
                worksheet.write(row, 5, incident.total_loss or 0, number_format)
                row += 1

    def _write_kris_sheet(self, workbook, risks, header_format, cell_format, number_format):
        """Écrit la feuille des KRI"""
        worksheet = workbook.add_worksheet('KRI')
        headers = ['Code risque', 'Risque', 'KRI', 'Valeur actuelle', 'Seuil rouge', 'Statut']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 18)

        status_formats = {
            'red': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#f8d7da', 'font_color': '#721c24',
                 'bold': True}),
            'amber': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#fff3cd', 'font_color': '#856404',
                 'bold': True}),
            'green': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#d4edda', 'font_color': '#155724',
                 'bold': True}),
        }

        row = 1
        for risk in risks:
            for kri in risk.kri_ids:
                worksheet.write(row, 0, risk.code or '', cell_format)
                worksheet.write(row, 1, risk.name or '', cell_format)
                worksheet.write(row, 2, kri.name or '', cell_format)
                worksheet.write(row, 3, kri.current_value or 0, number_format)
                worksheet.write(row, 4, kri.threshold_red or 0, number_format)
                status = kri.status or ''
                status_label = self._get_selection_label('status', status)
                status_format = status_formats.get(status, cell_format)
                worksheet.write(row, 5, status_label, status_format)
                row += 1

    def _write_actions_sheet(self, workbook, risks, header_format, cell_format, number_format, date_format):
        """Écrit la feuille des actions avec dates formatées"""
        worksheet = workbook.add_worksheet('Actions')
        headers = ['Code risque', 'Risque', 'Action', 'Responsable', 'Date échéance', 'Statut']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 18)

        action_status_formats = {
            'completed': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#d4edda', 'font_color': '#155724',
                 'bold': True}),
            'in_progress': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#fff3cd', 'font_color': '#856404',
                 'bold': True}),
            'pending': workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#f8d7da', 'font_color': '#721c24',
                 'bold': True}),
        }

        row = 1
        for risk in risks:
            for action in risk.action_plan_ids:
                worksheet.write(row, 0, risk.code or '', cell_format)
                worksheet.write(row, 1, risk.name or '', cell_format)
                worksheet.write(row, 2, action.name or '', cell_format)
                worksheet.write(row, 3, action.owner_id.name or '', cell_format)
                if action.deadline:
                    if isinstance(action.deadline, datetime):
                        worksheet.write_datetime(row, 4, action.deadline, date_format)
                    else:
                        worksheet.write(row, 4, action.deadline.strftime('%d/%m/%Y') if action.deadline else '',
                                        cell_format)
                else:
                    worksheet.write(row, 4, '', cell_format)
                status = action.state or ''
                status_label = self._get_selection_label('state', status)
                status_format = action_status_formats.get(status, cell_format)
                worksheet.write(row, 5, status_label, status_format)
                row += 1

    def _write_summary_sheet(self, workbook, risks, header_format, cell_format, number_format):
        """Écrit la feuille de synthèse avec couleurs"""
        worksheet = workbook.add_worksheet('Synthèse')

        worksheet.write(0, 0, 'Indicateur', header_format)
        worksheet.write(0, 1, 'Valeur', header_format)
        worksheet.set_column(0, 0, 35)
        worksheet.set_column(1, 1, 20)

        row = 1

        worksheet.write(row, 0, 'Total risques', cell_format)
        worksheet.write(row, 1, len(risks), number_format)
        row += 1

        levels = ['critical', 'high', 'medium', 'low']
        level_labels = {'critical': 'Risques critiques', 'high': 'Risques élevés',
                        'medium': 'Risques modérés', 'low': 'Risques faibles'}
        level_colors = {'critical': '#dc3545', 'high': '#fd7e14',
                        'medium': '#ffc107', 'low': '#28a745'}

        for level in levels:
            count = len(risks.filtered(lambda r: r.inherent_level == level))
            color_format = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': level_colors[level],
                'font_color': 'white' if level in ['critical', 'high'] else 'black',
                'bold': True
            })
            worksheet.write(row, 0, level_labels[level], cell_format)
            worksheet.write(row, 1, count, color_format)
            row += 1

        # STATISTIQUES PAR MACRO-PROCESSUS
        row += 1
        worksheet.write(row, 0, '--- STATISTIQUES PAR PROCESSUS ---', header_format)
        row += 1
        worksheet.write(row, 0, 'Processus', header_format)
        worksheet.write(row, 1, 'Nombre de risques', header_format)
        row += 1

        macro_stats = {}
        for risk in risks:
            macro_name = risk.macro_process_id.name or 'Sans processus'
            if macro_name not in macro_stats:
                macro_stats[macro_name] = 0
            macro_stats[macro_name] += 1

        for macro_name, count in sorted(macro_stats.items(), key=lambda x: x[1], reverse=True):
            worksheet.write(row, 0, macro_name, cell_format)
            worksheet.write(row, 1, count, number_format)
            row += 1

        # STATISTIQUES PAR PROCESSUS
        row += 1
        worksheet.write(row, 0, '--- STATISTIQUES PAR SOUS PROCESSUS ---', header_format)
        row += 1
        worksheet.write(row, 0, 'Sous Processus', header_format)
        worksheet.write(row, 1, 'Nombre de risques', header_format)
        row += 1

        process_stats = {}
        for risk in risks:
            process_name = risk.process_id.name or 'Sans sous processus'
            if process_name not in process_stats:
                process_stats[process_name] = 0
            process_stats[process_name] += 1

        for process_name, count in sorted(process_stats.items(), key=lambda x: x[1], reverse=True):
            worksheet.write(row, 0, process_name, cell_format)
            worksheet.write(row, 1, count, number_format)
            row += 1

        # STATISTIQUES PAR ACTIVITÉ
        row += 1
        worksheet.write(row, 0, '--- STATISTIQUES PAR ACTIVITÉ ---', header_format)
        row += 1
        worksheet.write(row, 0, 'Activité', header_format)
        worksheet.write(row, 1, 'Nombre de risques', header_format)
        row += 1

        activity_stats = {}
        for risk in risks:
            activity_name = risk.activity_id.name or 'Sans activité'
            if activity_name not in activity_stats:
                activity_stats[activity_name] = 0
            activity_stats[activity_name] += 1

        for activity_name, count in sorted(activity_stats.items(), key=lambda x: x[1], reverse=True):
            worksheet.write(row, 0, activity_name, cell_format)
            worksheet.write(row, 1, count, number_format)
            row += 1

        # Statistiques générales
        row += 1
        total_score = sum(risks.mapped('inherent_score') or [0])
        avg_score = total_score / len(risks) if risks else 0
        worksheet.write(row, 0, 'Score inhérent moyen', cell_format)
        worksheet.write(row, 1, round(avg_score, 2), number_format)
        row += 1

        total_residual = sum(risks.mapped('residual_score') or [0])
        avg_residual = total_residual / len(risks) if risks else 0
        worksheet.write(row, 0, 'Score résiduel moyen', cell_format)
        worksheet.write(row, 1, round(avg_residual, 2), number_format)
        row += 1

        stats = [
            ('Contrôles', len(risks.mapped('control_ids'))),
            ('Incidents', len(risks.mapped('incident_ids'))),
            ('KRI', len(risks.mapped('kri_ids'))),
            ('Plans d\'action', len(risks.mapped('action_plan_ids'))),
        ]
        for label, value in stats:
            worksheet.write(row, 0, label, cell_format)
            worksheet.write(row, 1, value, number_format)
            row += 1

        # Répartition des niveaux résiduels
        row += 1
        worksheet.write(row, 0, '--- RÉPARTITION DES NIVEAUX RÉSIDUELS ---', header_format)
        row += 1

        for level in levels:
            count = len(risks.filtered(lambda r: r.residual_level == level))
            color_format = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': level_colors[level],
                'font_color': 'white' if level in ['critical', 'high'] else 'black',
                'bold': True
            })
            worksheet.write(row, 0, f"Résiduel {level_labels[level]}", cell_format)
            worksheet.write(row, 1, count, color_format)
            row += 1

    def _get_matrix_color(self, score):
        """Retourne la couleur pour la matrice"""
        if score <= 5:
            return '#28a745'
        elif score <= 15:
            return '#ffc107'
        elif score <= 25:
            return '#fd7e14'
        else:
            return '#dc3545'

    def _get_selection_label(self, field_name, value):
        """Retourne le libellé d'une sélection"""
        if not value:
            return ''

        # Récupérer le champ
        field = self.env['risk.risk']._fields.get(field_name)
        if not field:
            return value

        # Gérer les sélections
        if hasattr(field, 'selection'):
            # Si c'est une fonction (selection dynamique), on l'appelle
            if callable(field.selection):
                try:
                    # Appeler la méthode de sélection avec le bon contexte
                    selection = field.selection(self.env['risk.risk'])
                    selection_dict = dict(selection)
                    return selection_dict.get(value, value)
                except Exception:
                    return value
            else:
                # Si c'est une liste de tuples
                try:
                    selection_dict = dict(field.selection)
                    return selection_dict.get(value, value)
                except ValueError:
                    return value

        return value

    def _get_effectiveness_label(self, value):
        """Retourne le libellé de l'efficacité des contrôles"""
        labels = {
            'high': 'Élevée',
            'medium': 'Moyenne',
            'low': 'Faible',
        }
        return labels.get(value, value or '')

    def _export_csv(self):
        """Export en CSV"""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        headers = [
            'Code', 'Nom du risque', 'Catégorie', 'Processus', 'Sous Processus', 'Activité',
            'Score inhérent', 'Niveau inhérent',
            "Niveau d'efficacité des contrôles",
            'Score résiduel', 'Niveau résiduel',
            'Statut', 'Propriétaire'
        ]
        writer.writerow(headers)

        for risk in self._get_risks():
            writer.writerow([
                risk.code or '',
                risk.name or '',
                risk.category_id.name or '',
                risk.macro_process_id.name or '',
                risk.process_id.name or '',
                risk.activity_id.name or '',
                risk.inherent_score or 0,
                self._get_selection_label('inherent_level', risk.inherent_level),
                self._get_control_level_label(risk.control_effectiveness_level),
                risk.residual_score or 0,
                self._get_selection_label('residual_level', risk.residual_level),
                self._get_selection_label('state', risk.state),
                risk.owner_id.name or '',
            ])

        file_data = base64.b64encode(output.getvalue().encode('utf-8'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"export_grc_{timestamp}.csv"

        self.write({
            'file_name': filename,
            'file_data': file_data,
            'state': 'done'
        })

        return self._open_result()

    def _export_json(self):
        """Export en JSON"""
        risks = self._get_risks()
        data = []

        for risk in risks:
            risk_data = {
                'code': risk.code or '',
                'name': risk.name or '',
                'category': risk.category_id.name or '',
                'subcategory': risk.subcategory_id.name or '',
                'type': self._get_selection_label('risk_type', risk.risk_type),
                'source': self._get_selection_label('risk_source', risk.risk_source),
                'state': self._get_selection_label('state', risk.state),
                'owner': risk.owner_id.name or '',
                # Hiérarchie
                'macro_process': risk.macro_process_id.name or '',
                'process': risk.process_id.name or '',
                'activity': risk.activity_id.name or '',
                # Inhérent
                'inherent_probability': risk.inherent_probability or '',
                'inherent_impact': risk.inherent_impact or '',
                'inherent_score': risk.inherent_score or 0,
                'inherent_level': self._get_selection_label('inherent_level', risk.inherent_level),
                # Contrôles
                'control_effectiveness': self._get_control_level_label(risk.control_effectiveness_level),
                # Résiduel
                'residual_score': risk.residual_score or 0,
                'residual_level': self._get_selection_label('residual_level', risk.residual_level),
                'active': risk.active,
                'last_review_date': risk.last_review_date.strftime('%d/%m/%Y') if risk.last_review_date else '',
                'next_review_date': risk.next_review_date.strftime('%d/%m/%Y') if risk.next_review_date else '',
                'controls': [{'name': c.name, 'type': c.control_type, 'effectiveness': c.effectiveness} for c in
                             risk.control_ids],
                'incidents_count': len(risk.incident_ids),
                'kris': [
                    {
                        'name': k.name,
                        'value': k.current_value,
                        'threshold_red': k.threshold_red,
                        'status': self._get_selection_label('status', k.status)
                    }
                    for k in risk.kri_ids
                ],
            }
            data.append(risk_data)

        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        file_data = base64.b64encode(json_data.encode('utf-8'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"export_grc_{timestamp}.json"

        self.write({
            'file_name': filename,
            'file_data': file_data,
            'state': 'done'
        })

        return self._open_result()

    def _export_xml(self):
        """Export en XML"""
        risks = self._get_risks()

        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<risques>')

        for risk in risks:
            xml.append(f'  <risque code="{risk.code or ""}">')
            xml.append(f'    <nom>{risk.name or ""}</nom>')
            xml.append(f'    <categorie>{risk.category_id.name or ""}</categorie>')
            xml.append(f'    <sous_categorie>{risk.subcategory_id.name or ""}</sous_categorie>')
            xml.append(f'    <type>{self._get_selection_label("risk_type", risk.risk_type)}</type>')
            xml.append(f'    <source>{self._get_selection_label("risk_source", risk.risk_source)}</source>')
            xml.append(f'    <statut>{self._get_selection_label("state", risk.state)}</statut>')
            xml.append(f'    <proprietaire>{risk.owner_id.name or ""}</proprietaire>')
            # Hiérarchie
            xml.append(f'    <macro_processus>{risk.macro_process_id.name or ""}</macro_processus>')
            xml.append(f'    <processus>{risk.process_id.name or ""}</processus>')
            xml.append(f'    <activite>{risk.activity_id.name or ""}</activite>')
            # Inhérent
            xml.append(f'    <probabilite_inherente>{risk.inherent_probability or ""}</probabilite_inherente>')
            xml.append(f'    <impact_inherent>{risk.inherent_impact or ""}</impact_inherent>')
            xml.append(f'    <score_inherent>{risk.inherent_score or 0}</score_inherent>')
            xml.append(f'    <niveau_inherent>{self._get_selection_label("inherent_level", risk.inherent_level)}</niveau_inherent>')
            # Contrôles
            xml.append(f'    <efficacite_controles>{self._get_control_level_label(risk.control_effectiveness_level)}</efficacite_controles>')
            # Résiduel
            xml.append(f'    <score_residuel>{risk.residual_score or 0}</score_residuel>')
            xml.append(f'    <niveau_residuel>{self._get_selection_label("residual_level", risk.residual_level)}</niveau_residuel>')
            xml.append(f'    <actif>{str(risk.active).lower()}</actif>')
            xml.append(
                f'    <derniere_revision>{risk.last_review_date.strftime("%d/%m/%Y") if risk.last_review_date else ""}</derniere_revision>')
            xml.append(
                f'    <prochaine_revision>{risk.next_review_date.strftime("%d/%m/%Y") if risk.next_review_date else ""}</prochaine_revision>')

            if risk.control_ids:
                xml.append('    <controles>')
                for control in risk.control_ids:
                    xml.append(
                        f'      <controle nom="{control.name}" type="{control.control_type}" efficacite="{control.effectiveness}"/>')
                xml.append('    </controles>')

            if risk.kri_ids:
                xml.append('    <kris>')
                for kri in risk.kri_ids:
                    xml.append(
                        f'      <kri nom="{kri.name}" valeur="{kri.current_value}" seuil_rouge="{kri.threshold_red}" statut="{self._get_selection_label("status", kri.status)}"/>')
                xml.append('    </kris>')

            xml.append('  </risque>')

        xml.append('</risques>')

        xml_data = '\n'.join(xml)
        file_data = base64.b64encode(xml_data.encode('utf-8'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"export_grc_{timestamp}.xml"

        self.write({
            'file_name': filename,
            'file_data': file_data,
            'state': 'done'
        })

        return self._open_result()

    def _open_result(self):
        """Ouvre la fenêtre de résultat"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Export terminé',
            'res_model': 'risk.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_download(self):
        """Télécharge le fichier"""
        self.ensure_one()
        if not self.file_data:
            raise UserError("Aucun fichier à télécharger.")

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/risk.export.wizard/{self.id}/file_data/{self.file_name}',
            'target': 'self',
        }


class RiskImportWizard(models.TransientModel):
    _name = 'risk.import.wizard'
    _description = "Assistant d'import des données GRC"

    file_name = fields.Char(string='Nom du fichier')
    file_data = fields.Binary(string='Fichier', required=True)
    import_type = fields.Selection([
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('csv', 'CSV'),
    ], string="Type d'import", default='json', required=True)
    dry_run = fields.Boolean(string='Mode simulation', default=True)
    import_log = fields.Text(string="Journal d'import")

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('done', 'Terminé'),
    ], string='Statut', default='draft')

    def action_import(self):
        """Exécute l'import"""
        self.ensure_one()

        if not self.file_data:
            raise UserError("Veuillez sélectionner un fichier à importer.")

        try:
            file_content = base64.b64decode(self.file_data).decode('utf-8')

            if self.import_type == 'json':
                result = self._import_json(file_content)
            elif self.import_type == 'xml':
                result = self._import_xml(file_content)
            elif self.import_type == 'csv':
                result = self._import_csv(file_content)
            else:
                raise UserError("Type d'import non supporté.")

            self.write({
                'import_log': f"✅ Import terminé avec succès !\n\n{result}",
                'state': 'done'
            })

        except Exception as e:
            self.import_log = f"❌ Erreur lors de l'import :\n{str(e)}"
            raise UserError(f"Erreur d'import : {str(e)}")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Import terminé',
            'res_model': 'risk.import.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def _import_json(self, content):
        """Import depuis JSON"""
        import json
        data = json.loads(content)

        if not isinstance(data, list):
            raise UserError("Le fichier JSON doit contenir une liste de risques.")

        created = 0
        updated = 0
        errors = []

        for item in data:
            try:
                existing = self.env['risk.risk'].search([('code', '=', item.get('code', ''))], limit=1)

                vals = {
                    'name': item.get('name', 'Risque importé'),
                    'code': item.get('code', ''),
                    'risk_type': item.get('type', ''),
                    'risk_source': item.get('source', ''),
                    'state': item.get('state', 'draft'),
                    'active': item.get('active', True),
                }

                # Hiérarchie
                if item.get('process'):
                    process = self.env['risk.process'].search([('name', '=', item.get('process'))], limit=1)
                    if process:
                        vals['process_id'] = process.id

                if item.get('activity'):
                    activity = self.env['risk.activity'].search([('name', '=', item.get('activity'))], limit=1)
                    if activity:
                        vals['activity_id'] = activity.id

                if existing:
                    existing.write(vals)
                    updated += 1
                else:
                    self.env['risk.risk'].create(vals)
                    created += 1

            except Exception as e:
                errors.append(f"Erreur sur {item.get('code', 'inconnu')}: {str(e)}")

        result = f"Créés: {created}\nMis à jour: {updated}"
        if errors:
            result += f"\n\nErreurs:\n" + "\n".join(errors)

        return result

    def _import_xml(self, content):
        """Import depuis XML"""
        import xml.etree.ElementTree as ET
        root = ET.fromstring(content)

        created = 0
        updated = 0
        errors = []

        for risk_elem in root.findall('risque'):
            try:
                code = risk_elem.get('code', '')
                name_elem = risk_elem.find('nom')
                state_elem = risk_elem.find('statut')
                process_elem = risk_elem.find('processus')
                activity_elem = risk_elem.find('activite')

                vals = {
                    'name': name_elem.text if name_elem is not None else 'Risque importé',
                    'code': code,
                    'state': state_elem.text if state_elem is not None else 'draft',
                }

                if process_elem is not None and process_elem.text:
                    process = self.env['risk.process'].search([('name', '=', process_elem.text)], limit=1)
                    if process:
                        vals['process_id'] = process.id

                if activity_elem is not None and activity_elem.text:
                    activity = self.env['risk.activity'].search([('name', '=', activity_elem.text)], limit=1)
                    if activity:
                        vals['activity_id'] = activity.id

                existing = self.env['risk.risk'].search([('code', '=', code)], limit=1)
                if existing:
                    existing.write(vals)
                    updated += 1
                else:
                    self.env['risk.risk'].create(vals)
                    created += 1

            except Exception as e:
                errors.append(f"Erreur sur {risk_elem.get('code', 'inconnu')}: {str(e)}")

        result = f"Créés: {created}\nMis à jour: {updated}"
        if errors:
            result += f"\n\nErreurs:\n" + "\n".join(errors)

        return result

    def _import_csv(self, content):
        """Import depuis CSV"""
        import csv
        from io import StringIO

        reader = csv.DictReader(StringIO(content))
        created = 0
        updated = 0
        errors = []

        for row in reader:
            try:
                vals = {
                    'name': row.get('Nom du risque', 'Risque importé'),
                    'code': row.get('Code', ''),
                    'state': row.get('Statut', 'draft'),
                }

                if row.get('Score inhérent'):
                    vals['inherent_score'] = int(row.get('Score inhérent'))

                if row.get('Processus'):
                    process = self.env['risk.process'].search([('name', '=', row.get('Processus'))], limit=1)
                    if process:
                        vals['process_id'] = process.id

                if row.get('Activité'):
                    activity = self.env['risk.activity'].search([('name', '=', row.get('Activité'))], limit=1)
                    if activity:
                        vals['activity_id'] = activity.id

                existing = self.env['risk.risk'].search([('code', '=', vals['code'])], limit=1)
                if existing:
                    existing.write(vals)
                    updated += 1
                else:
                    self.env['risk.risk'].create(vals)
                    created += 1

            except Exception as e:
                errors.append(f"Erreur sur la ligne: {str(e)}")

        result = f"Créés: {created}\nMis à jour: {updated}"
        if errors:
            result += f"\n\nErreurs:\n" + "\n".join(errors)

        return result