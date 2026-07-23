# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import io
import json
from datetime import datetime


class RiskHeatmapExportWizard(models.TransientModel):
    _name = 'risk.heatmap.export.wizard'
    _description = "Assistant d'export des matrices de risques"

    matrix_data = fields.Text(string='Données de la matrice inhérente')
    residual_matrix_data = fields.Text(string='Données de la matrice résiduelle')
    total_risks = fields.Integer(string='Total des risques')

    export_format = fields.Selection([
        ('png', 'PNG'),
        ('jpg', 'JPG'),
        ('pdf', 'PDF'),
    ], string='Format d\'export', default='png', required=True)

    file_name = fields.Char(string='Nom du fichier')
    file_data = fields.Binary(string='Fichier', attachment=True)

    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('done', 'Terminé'),
    ], string='Statut', default='draft')

    def action_export_matrices(self):
        """Exporter les matrices en image"""
        self.ensure_one()

        # Cette méthode sera appelée depuis le JavaScript
        # Elle génère les images des matrices et les assemble

        # Pour l'instant, on crée un fichier de rapport simple
        # Dans une implémentation réelle, on utiliserait html2canvas ou un service externe

        html_content = self._generate_report_html()

        # Convertir en PDF avec wkhtmltopdf
        # ou générer une image avec html2canvas

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"matrices_risques_{timestamp}.png"

        # Simuler une exportation
        # Dans la réalité, vous utiliseriez un service pour générer l'image

        self.write({
            'file_name': filename,
            'state': 'done'
        })

        return self._open_result()

    def _generate_report_html(self):
        """Génère le HTML du rapport"""
        matrix = json.loads(self.matrix_data) if self.matrix_data else {}
        residual = json.loads(self.residual_matrix_data) if self.residual_matrix_data else {}

        html = f'''
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 20px; }}
                .matrix-container {{ display: flex; gap: 40px; justify-content: center; flex-wrap: wrap; }}
                .matrix {{ border-collapse: collapse; }}
                .matrix th, .matrix td {{ border: 1px solid #ddd; padding: 8px; text-align: center; width: 40px; height: 40px; }}
                .matrix th {{ background: #1a237e; color: white; }}
                .matrix .label {{ background: #f5f5f5; font-weight: bold; }}
                .hm-red {{ background: #dc3545; color: white; }}
                .hm-orange {{ background: #fd7e14; color: white; }}
                .hm-yellow {{ background: #ffc107; color: black; }}
                .hm-green {{ background: #28a745; color: white; }}
                .hm-blue {{ background: #17a2b8; color: white; }}
                .title {{ text-align: center; color: #1a237e; margin-bottom: 15px; }}
            </style>
        </head>
        <body>
            <h1 class="title">📊 Matrices des Risques</h1>
            <p style="text-align:center;">Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            <p style="text-align:center;">Total des risques: {self.total_risks}</p>
            <div class="matrix-container">
                <div>
                    <h3 style="text-align:center;">🔥 Matrice Inhérente</h3>
                    <table class="matrix">
                        <tr><th></th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th></tr>
        '''

        for impact in range(5, 0, -1):
            html += f'<tr><td class="label">{impact}</td>'
            for prob in range(1, 6):
                value = matrix.get(str(impact), {}).get(str(prob), 0)
                score = impact * prob
                cls = self._get_heatmap_class(score)
                html += f'<td class="{cls}">{value}</td>'
            html += '</tr>'

        html += '''
                    </table>
                </div>
                <div>
                    <h3 style="text-align:center;">🔥 Matrice Résiduelle</h3>
                    <table class="matrix">
                        <tr><th></th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th></tr>
        '''

        for impact in range(5, 0, -1):
            html += f'<tr><td class="label">{impact}</td>'
            for prob in range(1, 6):
                value = residual.get(str(impact), {}).get(str(prob), 0)
                score = impact * prob
                cls = self._get_heatmap_class(score)
                html += f'<td class="{cls}">{value}</td>'
            html += '</tr>'

        html += f'''
                    </table>
                </div>
            </div>
            <div style="text-align:center;margin-top:20px;font-size:12px;color:#6c757d;">
                <span style="display:inline-block;width:20px;height:20px;border-radius:3px;background:#dc3545;vertical-align:middle;"></span> Critique
                <span style="display:inline-block;width:20px;height:20px;border-radius:3px;background:#fd7e14;vertical-align:middle;margin-left:15px;"></span> Élevé
                <span style="display:inline-block;width:20px;height:20px;border-radius:3px;background:#ffc107;vertical-align:middle;margin-left:15px;"></span> Moyen
                <span style="display:inline-block;width:20px;height:20px;border-radius:3px;background:#28a745;vertical-align:middle;margin-left:15px;"></span> Faible
            </div>
        </body>
        </html>
        '''

        return html

    def _get_heatmap_class(self, score):
        if score >= 20:
            return 'hm-red'
        elif score >= 12:
            return 'hm-orange'
        elif score >= 6:
            return 'hm-yellow'
        elif score >= 3:
            return 'hm-green'
        return 'hm-blue'

    def _open_result(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Export terminé',
            'res_model': 'risk.heatmap.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def action_download(self):
        self.ensure_one()
        if not self.file_data:
            raise UserError("Aucun fichier à télécharger.")

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/risk.heatmap.export.wizard/{self.id}/file_data/{self.file_name}',
            'target': 'self',
        }