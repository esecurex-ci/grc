from odoo import models, fields


class RiskMetricEngine(models.Model):
    _name = 'risk.metric.engine'
    _description = 'GRC Metric Engine'

    name = fields.Char(
        default='Metric Engine'
    )

    active = fields.Boolean(
        default=True
    )

    def action_calculate_grc_score(self):

        score = self.env[
            'risk.grc.score'
        ].create({

            'risk_score':
                self._calculate_risk_score(),

            'control_score':
                self._calculate_control_score(),

            'audit_score':
                self._calculate_audit_score(),

            'compliance_score':
                self._calculate_compliance_score(),

            'resilience_score':
                self._calculate_resilience_score(),

            'cyber_score':
                self._calculate_cyber_score()

        })

        return score

    def _calculate_risk_score(self):
        """Score GRC du volet Risques : moyenne, sur les évaluations
        existantes, d'un score dérivé du NIVEAU DE RISQUE RÉSIDUEL qualitatif
        (Faible/Modéré/Élevé) de chaque évaluation.

        ⚠️ Corrigé : cette méthode plantait avec
        "'risk.assessment' object has no attribute 'residual_score'" — ce
        champ n'a jamais existé sur risk.assessment, qui n'a volontairement
        PAS de score résiduel numérique (voir le champ 'risk_level' de ce
        modèle et son commentaire "Pas de score numérique pour le résiduel,
        conforme à l'échelle métier réelle"). C'est ce qui empêchait
        action_calculate_grc_score (et donc tout le Cockpit Exécutif, dont
        action_ensure_dashboard_snapshot qui l'appelle) de s'exécuter sans
        erreur, laissant tous les indicateurs à zéro.
        """
        assessments = self.env['risk.assessment'].search([])

        if not assessments:
            return 100

        level_scores = {'low': 100, 'medium': 60, 'high': 20}

        total = sum(
            level_scores.get(assessment.risk_level, 60)
            for assessment in assessments
        )

        return round(
            total / len(assessments),
            2
        )

    def _calculate_control_score(self):
        controls = self.env[
            'risk.control'
        ].search([])
        if not controls:
            return 0

        # effectiveness est catégoriel ('high'/'medium'/'low'/'not_tested') :
        # on utilise effectiveness_score, sa contrepartie numérique déjà calculée.
        return round(sum(controls.mapped('effectiveness_score')) / len(controls), 2)

    def _calculate_audit_score(self):

        findings = self.env[
            'risk.audit.finding'
        ].search([
            ('state', '!=', 'closed')
        ])

        total_findings = self.env[
            'risk.audit.finding'
        ].search_count([])

        if total_findings == 0:
            return 100

        return round(

            (
                    1 -
                    (
                            len(findings)
                            /
                            total_findings
                    )
            )
            * 100,

            2

        )

    def _calculate_compliance_score(self):

        assessments = self.env[
            'risk.compliance.assessment'
        ].search([])

        if not assessments:
            return 0

        return round(

            sum(
                assessments.mapped(
                    'compliance_percentage'
                )
            )
            /
            len(assessments),

            2

        )

    def _calculate_resilience_score(self):

        bcp_count = self.env[
            'risk.bcp.plan'
        ].search_count([])

        process_count = self.env[
            'risk.process'
        ].search_count([])

        if process_count == 0:
            return 0

        return round(

            (
                    bcp_count
                    /
                    process_count
            )
            * 100,

            2

        )

    def _calculate_cyber_score(self):

        cyber_incidents = self.env[
            'risk.incident'
        ].search_count([
            (
                'category_id.name',
                'ilike',
                'Cyber'
            )
        ])

        score = 100 - (
                cyber_incidents * 5
        )

        return max(
            score,
            0
        )

    def action_generate_history(self):

        latest_score = self.env[
            'risk.grc.score'
        ].search(
            [],
            order='assessment_date desc',
            limit=1
        )

        previous_history = self.env[
            'risk.grc.history'
        ].search(
            [],
            order='period_date desc',
            limit=1
        )

        history = self.env[
            'risk.grc.history'
        ].create({

            'name':
                latest_score.name,

            'period_date':
                latest_score.assessment_date,

            'grc_score_id':
                latest_score.id,

            'overall_score':
                latest_score.overall_score,

            'risk_score':
                latest_score.risk_score,

            'control_score':
                latest_score.control_score,

            'audit_score':
                latest_score.audit_score,

            'compliance_score':
                latest_score.compliance_score,

            'resilience_score':
                latest_score.resilience_score,

            'cyber_score':
                latest_score.cyber_score,

            'maturity_level':
                latest_score.maturity_level,

            'previous_history_id':
                previous_history.id
                if previous_history
                else False

        })

        return history

    def _calculate_risk_stats(self):
        """Statistiques de la section RISQUES du snapshot exécutif.

        Échelle réelle à 3 niveaux (pas de niveau 'Critique') :
        - critical_risks reprend les risques INHÉRENTS de niveau Élevé
          (mêmes "Risques Majeurs" que la heatmap : sommet réel de l'échelle).
        - high_risks reprend les risques RÉSIDUELS de niveau Élevé
          (mêmes "Priorités d'Action" que la heatmap : encore élevés après contrôles).
        - risks_over_appetite réutilise last_over_appetite, déjà calculé sur
          risk.risk à partir de la dernière évaluation approuvée (comparaison
          recalibrée sur l'échelle d'appétit à 5 niveaux, cf. risk.assessment).
        """
        risks = self.env['risk.risk'].search([('active', '=', True)])

        return {
            'total_risks': len(risks),
            'critical_risks': len(risks.filtered(lambda r: r.inherent_level == 'high')),
            'high_risks': len(risks.filtered(lambda r: r.residual_level == 'high')),
            'risks_over_appetite': len(risks.filtered('last_over_appetite')),
        }

    def _calculate_incident_stats(self):
        """Statistiques de la section INCIDENTS du snapshot exécutif."""
        incidents = self.env['risk.incident'].search([])

        return {
            'total_incidents': len(incidents),
            'open_incidents': len(incidents.filtered(lambda i: i.status != 'closed')),
            'critical_incidents': len(incidents.filtered(lambda i: i.severity == 'critical')),
            'operational_losses': sum(incidents.mapped('total_loss')),
        }

    def _calculate_audit_stats(self):
        """Statistiques de la section AUDIT du snapshot exécutif."""
        today = fields.Date.today()

        findings = self.env['risk.audit.finding'].search([])

        overdue_recommendations = self.env['risk.audit.recommendation'].search([
            ('target_date', '<', today),
            ('state', 'not in', ['verified', 'closed']),
        ])

        return {
            'total_findings': len(findings),
            'open_findings': len(findings.filtered(lambda f: f.state != 'closed')),
            'critical_findings': len(findings.filtered(lambda f: f.severity == 'critical')),
            'overdue_audit_actions': len(overdue_recommendations),
        }

    def _calculate_compliance_stats(self):
        """Statistiques de la section COMPLIANCE du snapshot exécutif.

        compliance_rate reprend le même calcul que _calculate_compliance_score
        (moyenne des compliance_percentage des évaluations) : c'est ce champ
        'compliance_rate' — et non 'compliance_score' — que le widget du
        Cockpit affiche dans "Taux de Conformité", d'où son 0% persistant
        tant qu'il n'était jamais renseigné lors de la génération du snapshot.
        """
        today = fields.Date.today()

        assessments = self.env['risk.compliance.assessment'].search([])

        non_compliant_requirements = len(
            assessments.filtered(lambda a: a.compliance_level == 'non_compliant').mapped('requirement_id')
        )

        overdue_plans = self.env['risk.compliance.action.plan'].search([
            ('target_date', '<', today),
            ('state', 'not in', ['completed', 'validated']),
        ])

        return {
            'compliance_rate': self._calculate_compliance_score(),
            'non_compliant_requirements': non_compliant_requirements,
            'overdue_compliance_actions': len(overdue_plans),
        }

    def _calculate_resilience_stats(self):
        """Statistiques de la section BCM/DRP du snapshot exécutif.

        Délègue entièrement à risk.continuity.dashboard.get_resilience_kpis()
        au lieu de recalculer ces taux avec sa propre formule. Avant cette
        correction, ce module comparait le nombre BRUT de risk.bcp.plan / de
        risk.drp.plan (tous états confondus, y compris les brouillons) au
        nombre de risk.process, sans aucun lien réel entre un PCA/PRA donné
        et le processus qu'il est censé couvrir — une formule différente de
        celle de risk.continuity.dashboard (qui, elle, ne comptait que les
        plans 'approved' rapportés au nombre de BIA). Les deux affichaient
        donc des pourcentages différents pour le même indicateur "Couverture
        PCA/PRA", visible ici au Cockpit et là au tableau de bord Résilience.
        """
        kpis = self.env['risk.continuity.dashboard'].get_resilience_kpis()

        return {
            'bcp_coverage_rate': kpis['bcp_coverage'],
            'drp_coverage_rate': kpis['drp_coverage'],
            'exercise_success_rate': kpis['exercise_success_rate'],
            # ✅ Nouvelle clé (le dict retourné par get_resilience_kpis en
            # porte plusieurs autres ; celle-ci est la plus pertinente pour
            # une vue exécutive : des actions correctives d'exercice encore
            # ouvertes, non closes).
            'open_resilience_actions_count': kpis['open_corrective_actions_count'],
        }

    def _calculate_crisis_stats(self):
        """Statistiques de la section GESTION DE CRISE du snapshot exécutif."""
        crises = self.env['risk.crisis'].search([])

        def _avg_hours(pairs):
            durations = [
                (end - start).total_seconds() / 3600.0
                for start, end in pairs
                if start and end and end > start
            ]
            return round(sum(durations) / len(durations), 2) if durations else 0

        return {
            'crisis_count': len(crises),
            'average_detection_time': _avg_hours([(c.declaration_date, c.start_date) for c in crises]),
            'average_recovery_time': _avg_hours([(c.start_date, c.resolution_date) for c in crises]),
            'average_closure_time': _avg_hours([(c.declaration_date, c.end_date) for c in crises]),
        }

    def _calculate_control_kri_stats(self):
        """Statistiques de la section CONTRÔLES & KRI du snapshot exécutif."""
        controls = self.env['risk.control'].search([])

        alerts = self.env['risk.kri.alert'].search_count([
            ('resolved', '=', False),
        ])

        kris = self.env['risk.kri'].search([])

        return {
            'control_score': self._calculate_control_score(),
            'total_controls': len(controls),
            'ineffective_controls': len(controls.filtered(lambda c: c.effectiveness == 'low')),
            'active_kri_alerts': alerts,
            'kri_over_appetite_count': len(kris.filtered('over_appetite')),
        }

    def _calculate_governance_stats(self):
        """Statistiques de la section GOUVERNANCE (documents & politiques)."""
        today = fields.Date.today()

        documents = self.env['risk.document'].search([])

        overdue_policies = self.env['risk.policy'].search_count([
            ('next_review_date', '<', today),
            ('state', 'not in', ['archived']),
        ])

        return {
            'total_documents': len(documents),
            'documents_review_overdue': len(documents.filtered(lambda d: d.review_status == 'overdue')),
            'expired_documents': len(documents.filtered('expired')),
            'policies_review_overdue': overdue_policies,
        }

    def _calculate_reporting_stats(self):
        """Statistiques de la section REPORTING (rapports réglementaires et conseil)."""
        reports = self.env['risk.regulatory.report'].search([])

        return {
            'total_regulatory_reports': len(reports),
            'pending_regulatory_reports': len(reports.filtered(lambda r: r.state == 'draft')),
            'total_board_reports': self.env['risk.board.report'].search_count([]),
        }

    def _compute_snapshot_vals(self):
        """Calcule l'ensemble des valeurs (vals dict) du snapshot exécutif du
        jour, à partir des données ACTUELLES de tous les modules du GRC.

        Isolé dans sa propre méthode pour pouvoir être appelé aussi bien
        pour CRÉER un nouveau snapshot que pour RAFRAÎCHIR (write) le
        snapshot du jour déjà existant — voir action_ensure_dashboard_snapshot,
        qui a besoin de recalculer les valeurs à chaque ouverture du Cockpit
        et non de se contenter de renvoyer un snapshot figé.
        """
        latest_grc = self.env[
            'risk.grc.score'
        ].search(
            [],
            limit=1,
            order='assessment_date desc'
        )

        history = self.env[
            'risk.grc.history'
        ].search(
            [],
            limit=1,
            order='period_date desc'
        )

        risk_stats = self._calculate_risk_stats()
        incident_stats = self._calculate_incident_stats()
        audit_stats = self._calculate_audit_stats()
        compliance_stats = self._calculate_compliance_stats()
        resilience_stats = self._calculate_resilience_stats()
        crisis_stats = self._calculate_crisis_stats()
        control_kri_stats = self._calculate_control_kri_stats()
        governance_stats = self._calculate_governance_stats()
        reporting_stats = self._calculate_reporting_stats()

        return {

            'name':
                f"Dashboard {fields.Date.today()}",

            'snapshot_date':
                fields.Date.today(),

            'grc_score_id':
                latest_grc.id,

            'grc_history_id':
                history.id,

            'overall_score':
                latest_grc.overall_score,

            'risk_score':
                latest_grc.risk_score,

            'compliance_score':
                latest_grc.compliance_score,

            'audit_score':
                latest_grc.audit_score,

            'resilience_score':
                latest_grc.resilience_score,

            'cyber_score':
                latest_grc.cyber_score,

            'maturity_level':
                latest_grc.maturity_level,

            'total_risks':
                risk_stats['total_risks'],

            'critical_risks':
                risk_stats['critical_risks'],

            'high_risks':
                risk_stats['high_risks'],

            'risks_over_appetite':
                risk_stats['risks_over_appetite'],

            # ---- Incidents ----
            'total_incidents':
                incident_stats['total_incidents'],
            'open_incidents':
                incident_stats['open_incidents'],
            'critical_incidents':
                incident_stats['critical_incidents'],
            'operational_losses':
                incident_stats['operational_losses'],

            # ---- Audit ----
            'total_findings':
                audit_stats['total_findings'],
            'open_findings':
                audit_stats['open_findings'],
            'critical_findings':
                audit_stats['critical_findings'],
            'overdue_audit_actions':
                audit_stats['overdue_audit_actions'],

            # ---- Conformité ----
            'compliance_rate':
                compliance_stats['compliance_rate'],
            'non_compliant_requirements':
                compliance_stats['non_compliant_requirements'],
            'overdue_compliance_actions':
                compliance_stats['overdue_compliance_actions'],

            # ---- Résilience (BCM/DRP) ----
            'bcp_coverage_rate':
                resilience_stats['bcp_coverage_rate'],
            'drp_coverage_rate':
                resilience_stats['drp_coverage_rate'],
            'exercise_success_rate':
                resilience_stats['exercise_success_rate'],
            'open_resilience_actions_count':
                resilience_stats['open_resilience_actions_count'],

            # ---- Gestion de Crise ----
            'crisis_count':
                crisis_stats['crisis_count'],
            'average_detection_time':
                crisis_stats['average_detection_time'],
            'average_recovery_time':
                crisis_stats['average_recovery_time'],
            'average_closure_time':
                crisis_stats['average_closure_time'],

            # ---- Contrôles & KRI ----
            'control_score':
                control_kri_stats['control_score'],
            'total_controls':
                control_kri_stats['total_controls'],
            'ineffective_controls':
                control_kri_stats['ineffective_controls'],
            'active_kri_alerts':
                control_kri_stats['active_kri_alerts'],
            'kri_over_appetite_count':
                control_kri_stats['kri_over_appetite_count'],

            # ---- Gouvernance ----
            'total_documents':
                governance_stats['total_documents'],
            'documents_review_overdue':
                governance_stats['documents_review_overdue'],
            'expired_documents':
                governance_stats['expired_documents'],
            'policies_review_overdue':
                governance_stats['policies_review_overdue'],

            # ---- Reporting ----
            'total_regulatory_reports':
                reporting_stats['total_regulatory_reports'],
            'pending_regulatory_reports':
                reporting_stats['pending_regulatory_reports'],
            'total_board_reports':
                reporting_stats['total_board_reports'],

        }

    def action_generate_dashboard_snapshot(self):
        """Crée un NOUVEAU snapshot exécutif (utilisé notamment pour garder
        un historique explicite, par ex. depuis un bouton manuel)."""
        return self.env['risk.executive.dashboard.snapshot'].create(
            self._compute_snapshot_vals()
        )

    def action_ensure_dashboard_snapshot(self):
        """Retourne le snapshot exécutif du jour, en le rafraîchissant.

        Le Cockpit Exécutif GRC affichait des KPI figés à zéro car le
        snapshot n'était jamais créé automatiquement (il fallait déclencher
        manuellement 'action_generate_dashboard_snapshot'). Cette méthode est
        appelée par le widget à chaque ouverture du tableau de bord.

        ⚠️ Elle ne se contente PAS de réutiliser tel quel un snapshot déjà
        existant pour aujourd'hui : elle recalcule systématiquement les
        valeurs et les écrit (write) sur ce snapshot du jour. Sans ce
        rafraîchissement, un snapshot créé tôt dans la journée (avant une
        mise à jour de risques/incidents/contrôles, ou avant l'ajout d'un
        nouveau calcul dans ce module) restait figé avec des valeurs
        obsolètes pour le reste de la journée — c'est exactement ce qui
        provoquait la réapparition d'indicateurs à 0 après une mise à jour.
        """
        today = fields.Date.today()

        snapshot = self.env['risk.executive.dashboard.snapshot'].search(
            [('snapshot_date', '=', today)], limit=1, order='id desc'
        )

        latest_grc = self.env['risk.grc.score'].search(
            [], limit=1, order='assessment_date desc'
        )
        if not latest_grc or latest_grc.assessment_date != today:
            self.action_calculate_grc_score()

        vals = self._compute_snapshot_vals()

        if snapshot:
            snapshot.write(vals)
            return snapshot

        return self.env['risk.executive.dashboard.snapshot'].create(vals)

