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
    _description = 'Assistant d\'export des données GRC'

    # Options d'export
    export_type = fields.Selection([
        ('risks', 'Risques uniquement'),
        ('risks_with_relations', 'Risques avec relations'),
        ('full', 'Données complètes'),
        ('matrix', 'Matrice des risques'),
    ], string='Type d\'export', default='risks', required=True)

    export_format = fields.Selection([
        ('xlsx', 'Excel (.xlsx)'),
        ('csv', 'CSV'),
        ('json', 'JSON'),
        ('xml', 'XML'),
    ], string='Format d\'export', default='xlsx', required=True)

    include_relations = fields.Boolean(string='Inclure les relations', default=True)
    include_historical = fields.Boolean(string='Inclure l\'historique', default=False)

    file_name = fields.Char(string='Nom du fichier')
    file_data = fields.Binary(string='Fichier', attachment=True)

    # ✅ AJOUT DU CHAMP STATE MANQUANT
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('done', 'Terminé'),
    ], string='Statut', default='draft')

    # Statistiques pour l'aperçu
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

    def _export_xlsx(self):
        """Export Excel complet"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Formats
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

        risks = self._get_risks()

        # Feuille principale : Risques
        worksheet = workbook.add_worksheet('Risques')
        self._write_risks_sheet(worksheet, risks, header_format, cell_format, number_format)

        # Feuilles supplémentaires
        if self.export_type in ['risks_with_relations', 'full']:
            self._write_controls_sheet(workbook, risks, header_format, cell_format, number_format)
            self._write_incidents_sheet(workbook, risks, header_format, cell_format, number_format)
            self._write_kris_sheet(workbook, risks, header_format, cell_format, number_format)

        if self.export_type == 'full':
            self._write_actions_sheet(workbook, risks, header_format, cell_format, number_format)

        if self.export_type == 'matrix':
            # Remplacer la première feuille par la matrice
            workbook.remove_sheet(worksheet)
            worksheet = workbook.add_worksheet('Matrice')
            self._write_matrix_sheet(worksheet, risks, header_format, cell_format, number_format)

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
            'state': 'done'  # ✅ Mise à jour du statut
        })

        return self._open_result()

    def _write_risks_sheet(self, worksheet, risks, header_format, cell_format, number_format):
        """Écrit la feuille des risques"""
        headers = [
            'Code', 'Nom', 'Catégorie', 'Sous-catégorie',
            'Type', 'Source', 'Statut', 'Propriétaire',
            'Probabilité inhérente', 'Impact inhérent',
            'Score inhérent', 'Niveau inhérent',
            'Probabilité résiduelle', 'Impact résiduel',
            'Score résiduel', 'Niveau résiduel',
            'Dernière révision', 'Prochaine révision',
            'Société', 'Actif'
        ]

        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 18)

        row = 1
        for risk in risks:
            col = 0
            worksheet.write(row, col, risk.code or '', cell_format)
            col += 1
            worksheet.write(row, col, risk.name or '', cell_format)
            col += 1
            worksheet.write(row, col, risk.category_id.name or '', cell_format)
            col += 1
            worksheet.write(row, col, risk.subcategory_id.name or '', cell_format)
            col += 1
            worksheet.write(row, col, self._get_selection_label('risk_type', risk.risk_type), cell_format)
            col += 1
            worksheet.write(row, col, self._get_selection_label('risk_source', risk.risk_source), cell_format)
            col += 1
            worksheet.write(row, col, self._get_selection_label('state', risk.state), cell_format)
            col += 1
            worksheet.write(row, col, risk.owner_id.name or '', cell_format)
            col += 1
            worksheet.write(row, col, risk.inherent_probability or '', number_format)
            col += 1
            worksheet.write(row, col, risk.inherent_impact or '', number_format)
            col += 1
            worksheet.write(row, col, risk.inherent_score or 0, number_format)
            col += 1
            worksheet.write(row, col, risk.inherent_level or '', cell_format)
            col += 1
            worksheet.write(row, col, risk.residual_probability or '', number_format)
            col += 1
            worksheet.write(row, col, risk.residual_impact or '', number_format)
            col += 1
            worksheet.write(row, col, risk.residual_score or 0, number_format)
            col += 1
            worksheet.write(row, col, risk.residual_level or '', cell_format)
            col += 1
            worksheet.write(row, col, risk.last_review_date or '', cell_format)
            col += 1
            worksheet.write(row, col, risk.next_review_date or '', cell_format)
            col += 1
            worksheet.write(row, col, risk.company_id.name or '', cell_format)
            col += 1
            worksheet.write(row, col, 'Oui' if risk.active else 'Non', cell_format)
            row += 1

    def _write_matrix_sheet(self, worksheet, risks, header_format, cell_format, number_format):
        """Écrit la feuille de la matrice 5x5"""
        # En-têtes
        worksheet.write(0, 0, 'Probabilité ↓ / Impact →', header_format)
        for i in range(1, 6):
            worksheet.write(0, i, str(i), header_format)
        worksheet.write(0, 6, 'Total', header_format)

        # Matrice
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
                # ✅ Utilisation de workbook.add_format
                cell_format_color = workbook.add_format({
                    'align': 'center', 'valign': 'vcenter', 'border': 1,
                    'bg_color': color, 'font_color': 'white' if score > 12 else 'black',
                    'bold': True
                })
                worksheet.write(row, impact, count, cell_format_color)
            worksheet.write(row, 6, total_row, number_format)
            row += 1

        # Total par impact
        worksheet.write(row, 0, 'Total', header_format)
        for impact in range(1, 6):
            total_col = sum(matrix.get(f"{prob}_{impact}", 0) for prob in range(1, 6))
            worksheet.write(row, impact, total_col, number_format)
        worksheet.write(row, 6, len(risks), number_format)

        # Légende
        worksheet.write(row + 2, 0, 'Légende :', header_format)
        legend_colors = [
            ('Faible (1-4)', '#28a745'),
            ('Moyen (5-9)', '#ffc107'),
            ('Élevé (10-16)', '#fd7e14'),
            ('Critique (17-25)', '#dc3545'),
        ]
        for i, (label, color) in enumerate(legend_colors):
            cell_format_color = workbook.add_format({
                'align': 'center', 'valign': 'vcenter', 'border': 1,
                'bg_color': color, 'font_color': 'white' if i > 1 else 'black'
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

        row = 1
        for risk in risks:
            for control in risk.control_ids:
                worksheet.write(row, 0, risk.code or '', cell_format)
                worksheet.write(row, 1, risk.name or '', cell_format)
                worksheet.write(row, 2, control.name or '', cell_format)
                worksheet.write(row, 3, control.control_type or '', cell_format)
                worksheet.write(row, 4, control.effectiveness or '', cell_format)
                worksheet.write(row, 5, control.state or '', cell_format)
                row += 1

    def _write_incidents_sheet(self, workbook, risks, header_format, cell_format, number_format):
        """Écrit la feuille des incidents"""
        worksheet = workbook.add_worksheet('Incidents')
        headers = ['Code risque', 'Risque', 'Incident', 'Date', 'Gravité', 'Perte']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 18)

        row = 1
        for risk in risks:
            for incident in risk.incident_ids:
                worksheet.write(row, 0, risk.code or '', cell_format)
                worksheet.write(row, 1, risk.name or '', cell_format)
                worksheet.write(row, 2, incident.name or '', cell_format)
                worksheet.write(row, 3, incident.incident_date or '', cell_format)
                worksheet.write(row, 4, incident.severity or '', cell_format)
                worksheet.write(row, 5, incident.total_loss or 0, number_format)
                row += 1

    def _write_kris_sheet(self, workbook, risks, header_format, cell_format, number_format):
        """Écrit la feuille des KRI"""
        worksheet = workbook.add_worksheet('KRI')
        headers = ['Code risque', 'Risque', 'KRI', 'Valeur', 'Seuil', 'Statut']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 18)

        row = 1
        for risk in risks:
            for kri in risk.kri_ids:
                worksheet.write(row, 0, risk.code or '', cell_format)
                worksheet.write(row, 1, risk.name or '', cell_format)
                worksheet.write(row, 2, kri.name or '', cell_format)
                worksheet.write(row, 3, kri.current_value or 0, number_format)
                worksheet.write(row, 4, kri.threshold or 0, number_format)
                worksheet.write(row, 5, kri.status or '', cell_format)
                row += 1

    def _write_actions_sheet(self, workbook, risks, header_format, cell_format, number_format):
        """Écrit la feuille des actions"""
        worksheet = workbook.add_worksheet('Actions')
        headers = ['Code risque', 'Risque', 'Action', 'Responsable', 'Date échéance', 'Statut']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
            worksheet.set_column(col, col, 18)

        row = 1
        for risk in risks:
            for action in risk.action_ids:
                worksheet.write(row, 0, risk.code or '', cell_format)
                worksheet.write(row, 1, risk.name or '', cell_format)
                worksheet.write(row, 2, action.name or '', cell_format)
                worksheet.write(row, 3, action.responsible_id.name or '', cell_format)
                worksheet.write(row, 4, action.deadline or '', cell_format)
                worksheet.write(row, 5, action.state or '', cell_format)
                row += 1

    def _write_summary_sheet(self, workbook, risks, header_format, cell_format, number_format):
        """Écrit la feuille de synthèse"""
        worksheet = workbook.add_worksheet('Synthèse')

        worksheet.write(0, 0, 'Indicateur', header_format)
        worksheet.write(0, 1, 'Valeur', header_format)
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, 1, 20)

        row = 1
        stats = [
            ('Total risques', len(risks)),
            ('Risques critiques', len(risks.filtered(lambda r: r.inherent_level == 'critical'))),
            ('Risques élevés', len(risks.filtered(lambda r: r.inherent_level == 'high'))),
            ('Risques moyens', len(risks.filtered(lambda r: r.inherent_level == 'medium'))),
            ('Risques faibles', len(risks.filtered(lambda r: r.inherent_level == 'low'))),
            ('Contrôles', len(risks.mapped('control_ids'))),
            ('Incidents', len(risks.mapped('incident_ids'))),
            ('KRI', len(risks.mapped('kri_ids'))),
            ('Actions', len(risks.mapped('action_ids'))),
        ]

        for label, value in stats:
            worksheet.write(row, 0, label, cell_format)
            worksheet.write(row, 1, value, number_format)
            row += 1

        total_score = sum(risks.mapped('inherent_score') or [0])
        avg_score = total_score / len(risks) if risks else 0
        worksheet.write(row, 0, 'Score moyen', cell_format)
        worksheet.write(row, 1, round(avg_score, 2), number_format)

    def _get_matrix_color(self, score):
        """Retourne la couleur pour la matrice"""
        if score <= 4:
            return '#28a745'
        elif score <= 9:
            return '#ffc107'
        elif score <= 16:
            return '#fd7e14'
        else:
            return '#dc3545'

    def _get_selection_label(self, field_name, value):
        """Retourne le libellé d'une sélection"""
        if not value:
            return ''
        field = self.env['risk.risk']._fields.get(field_name)
        if field and hasattr(field, 'selection'):
            selection = dict(field.selection)
            return selection.get(value, value)
        return value

    def _export_csv(self):
        """Export en CSV"""
        import csv
        from io import StringIO

        output = StringIO()
        writer = csv.writer(output)

        headers = ['Code', 'Nom', 'Catégorie', 'Score', 'Niveau', 'Statut']
        writer.writerow(headers)

        for risk in self._get_risks():
            writer.writerow([
                risk.code or '',
                risk.name or '',
                risk.category_id.name or '',
                risk.inherent_score or 0,
                risk.inherent_level or '',
                risk.state or '',
            ])

        file_data = base64.b64encode(output.getvalue().encode('utf-8'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"export_grc_{timestamp}.csv"

        self.write({
            'file_name': filename,
            'file_data': file_data,
            'state': 'done'  # ✅ Mise à jour du statut
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
                'type': risk.risk_type or '',
                'source': risk.risk_source or '',
                'state': risk.state or '',
                'owner': risk.owner_id.name or '',
                'inherent_score': risk.inherent_score or 0,
                'inherent_level': risk.inherent_level or '',
                'residual_score': risk.residual_score or 0,
                'residual_level': risk.residual_level or '',
                'active': risk.active,
                'controls': [c.name for c in risk.control_ids],
                'incidents_count': len(risk.incident_ids),
                'kris': [k.name for k in risk.kri_ids],
            }
            data.append(risk_data)

        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        file_data = base64.b64encode(json_data.encode('utf-8'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"export_grc_{timestamp}.json"

        self.write({
            'file_name': filename,
            'file_data': file_data,
            'state': 'done'  # ✅ Mise à jour du statut
        })

        return self._open_result()

    def _export_xml(self):
        """Export en XML"""
        risks = self._get_risks()

        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<risks>')

        for risk in risks:
            xml.append(f'  <risk code="{risk.code or ""}">')
            xml.append(f'    <name>{risk.name or ""}</name>')
            xml.append(f'    <category>{risk.category_id.name or ""}</category>')
            xml.append(f'    <state>{risk.state or ""}</state>')
            xml.append(f'    <inherent_score>{risk.inherent_score or 0}</inherent_score>')
            xml.append(f'    <inherent_level>{risk.inherent_level or ""}</inherent_level>')
            xml.append('  </risk>')

        xml.append('</risks>')

        xml_data = '\n'.join(xml)
        file_data = base64.b64encode(xml_data.encode('utf-8'))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"export_grc_{timestamp}.xml"

        self.write({
            'file_name': filename,
            'file_data': file_data,
            'state': 'done'  # ✅ Mise à jour du statut
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
    _description = 'Assistant d\'import des données GRC'

    file_name = fields.Char(string='Nom du fichier')
    file_data = fields.Binary(string='Fichier', required=True)
    import_type = fields.Selection([
        ('json', 'JSON'),
        ('xml', 'XML'),
        ('csv', 'CSV'),
    ], string='Type d\'import', default='json', required=True)
    dry_run = fields.Boolean(string='Mode simulation', default=True)
    import_log = fields.Text(string='Journal d\'import')

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
                    'inherent_score': int(item.get('inherent_score', 0)),
                    'inherent_level': item.get('inherent_level', ''),
                    'active': item.get('active', True),
                }

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

        for risk_elem in root.findall('risk'):
            try:
                code = risk_elem.get('code', '')
                name = risk_elem.find('name')
                state = risk_elem.find('state')
                score = risk_elem.find('inherent_score')

                vals = {
                    'name': name.text if name is not None else 'Risque importé',
                    'code': code,
                    'state': state.text if state is not None else 'draft',
                }

                if score is not None and score.text:
                    vals['inherent_score'] = int(score.text)

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
                    'name': row.get('Nom', 'Risque importé'),
                    'code': row.get('Code', ''),
                    'state': row.get('Statut', 'draft'),
                }

                if row.get('Score'):
                    vals['inherent_score'] = int(row.get('Score'))

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