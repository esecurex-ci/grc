from datetime import timedelta

from odoo import models, fields, api


class RiskContinuityDashboard(models.Model):
    _name = 'risk.continuity.dashboard'
    _description = 'Business Continuity Dashboard'

    name = fields.Char(
        default='Business Continuity Dashboard'
    )

    avg_rto = fields.Float(
        compute='_compute_dashboard'
    )

    avg_rpo = fields.Float(
        compute='_compute_dashboard'
    )

    avg_mtd = fields.Float(
        compute='_compute_dashboard'
    )

    exercise_count = fields.Integer(
        compute='_compute_dashboard'
    )

    bcp_coverage = fields.Float(
        compute='_compute_dashboard'
    )

    drp_coverage = fields.Float(
        compute='_compute_dashboard'
    )

    @api.model
    def get_resilience_kpis(self):
        """Calcule tous les indicateurs Résilience (PCA/PRA/BIA/Exercices) à
        partir d'une SEULE définition, partagée par ce tableau de bord,
        risk.metric.engine (widget Cockpit, Executive Dashboard Snapshot,
        GRC History) et le tableau de bord OWL "Résilience".

        Avant cette refonte, deux formules différentes et non reliées
        coexistaient pour "couverture PCA/PRA" : l'une ici (BCP/DRP approuvés
        rapportés au nombre total de BIA, tous états confondus), l'autre dans
        risk.metric.engine._calculate_resilience_stats (BCP/DRP, tous états
        confondus, rapportés au nombre de risk.process) — ce qui affichait
        deux pourcentages différents pour ce qui était présenté comme le même
        indicateur, à deux endroits de l'application. Centraliser le calcul
        ici élimine ce risque de divergence.

        Définition retenue :
        - Un "processus critique" est un processus disposant d'au moins une
          BIA à l'état 'approved' (le processus a été formellement identifié
          comme nécessitant une analyse d'impact — une BIA encore en
          brouillon ne suffit pas à qualifier le processus de critique).
        - Il est "couvert PCA" s'il dispose d'au moins un risk.bcp.plan à
          l'état 'approved' pour ce même process_id — un vrai lien entre les
          deux modèles (tous deux ont un process_id), au lieu d'une simple
          comparaison de décomptes globaux qui pouvait afficher 100% de
          couverture sans qu'aucun PCA ne corresponde réellement à une BIA.
        - Un "actif en périmètre PRA" est un risk.asset actif (active=True).
          risk.drp.plan n'a pas de lien vers risk.process/risk.bia dans ce
          modèle de données (seulement un system_id vers risk.asset) : le
          périmètre pertinent pour une reprise après sinistre est le parc
          d'actifs IT, pas les processus métier. Il est "couvert PRA" s'il
          dispose d'au moins un risk.drp.plan à l'état 'approved' pour ce
          même system_id.
        - Les moyennes RTO/RPO/MTD ne portent que sur les activités critiques
          (risk.bia.activity) de BIA elles-mêmes à l'état 'approved' :
          inclure les activités d'une BIA encore en brouillon ou déjà
          archivée fausserait ces moyennes avec des données non validées.
        """
        Bia = self.env['risk.bia']
        Bcp = self.env['risk.bcp.plan']
        Drp = self.env['risk.drp.plan']
        Asset = self.env['risk.asset']
        Activity = self.env['risk.bia.activity']
        Exercise = self.env['risk.exercise']

        approved_bia = Bia.search([('state', '=', 'approved')])
        critical_process_ids = set(approved_bia.mapped('process_id').ids)

        approved_bcp = Bcp.search([('state', '=', 'approved')])
        covered_process_ids = set(
            approved_bcp
            .filtered(lambda b: b.process_id.id in critical_process_ids)
            .mapped('process_id').ids
        )
        uncovered_process_ids = list(critical_process_ids - covered_process_ids)

        critical_asset_ids = set(Asset.search([('active', '=', True)]).ids)
        approved_drp = Drp.search([('state', '=', 'approved')])
        covered_asset_ids = set(
            approved_drp
            .filtered(lambda d: d.system_id.id in critical_asset_ids)
            .mapped('system_id').ids
        )
        uncovered_asset_ids = list(critical_asset_ids - covered_asset_ids)

        bcp_coverage = (
            len(covered_process_ids) * 100.0 / len(critical_process_ids)
            if critical_process_ids else 0.0
        )
        drp_coverage = (
            len(covered_asset_ids) * 100.0 / len(critical_asset_ids)
            if critical_asset_ids else 0.0
        )

        activities = Activity.search([('bia_id', 'in', approved_bia.ids)]) if approved_bia else Activity.browse()

        if activities:
            avg_rto = sum(activities.mapped('rto_hours')) / len(activities)
            avg_rpo = sum(activities.mapped('rpo_hours')) / len(activities)
            avg_mtd = sum(activities.mapped('mtd_hours')) / len(activities)
        else:
            avg_rto = avg_rpo = avg_mtd = 0.0

        completed_exercises = Exercise.search([('state', '=', 'completed')])
        if completed_exercises:
            successful = completed_exercises.filtered(
                lambda e: not e.finding_ids.filtered(
                    lambda f: f.severity in ('high', 'critical')
                )
            )
            exercise_success_rate = len(successful) * 100.0 / len(completed_exercises)
        else:
            exercise_success_rate = 0.0

        # ------------------------------------------------------------------
        # ✅ Nouveaux indicateurs — ajoutés en fin de dict, aucune clé
        # existante n'est retirée ni renommée, pour ne rien casser côté
        # risk.metric.engine ni du tableau de bord OWL Résilience qui lisent
        # déjà les clés ci-dessus.
        # ------------------------------------------------------------------

        stale_cutoff = fields.Date.today() - timedelta(days=365)

        stale_bcp_ids = approved_bcp.filtered(
            lambda b: not b.last_test_date or b.last_test_date < stale_cutoff
        ).ids
        stale_drp_ids = approved_drp.filtered(
            lambda d: not d.last_test_date or d.last_test_date < stale_cutoff
        ).ids

        all_findings = self.env['risk.exercise.finding'].search([])
        open_corrective_actions = all_findings.filtered(lambda f: f.state != 'closed')
        overdue_corrective_actions = open_corrective_actions.filtered(
            lambda f: f.target_date and f.target_date < fields.Date.today()
        )

        inconsistent_activities = activities.filtered('rto_exceeds_mtd')

        return {
            'total_bia': Bia.search_count([]),
            'approved_bia_count': len(approved_bia),
            'total_bcp': Bcp.search_count([]),
            'approved_bcp_count': len(approved_bcp),
            'total_drp': Drp.search_count([]),
            'approved_drp_count': len(approved_drp),
            'total_assets': len(critical_asset_ids),
            'critical_process_count': len(critical_process_ids),
            'covered_process_count': len(covered_process_ids),
            'uncovered_process_ids': uncovered_process_ids,
            'covered_asset_count': len(covered_asset_ids),
            'uncovered_asset_ids': uncovered_asset_ids,
            'bcp_coverage': round(bcp_coverage, 2),
            'drp_coverage': round(drp_coverage, 2),
            'avg_rto': round(avg_rto, 2),
            'avg_rpo': round(avg_rpo, 2),
            'avg_mtd': round(avg_mtd, 2),
            'exercise_count': len(completed_exercises),
            'total_exercise_count': Exercise.search_count([]),
            'exercise_success_rate': round(exercise_success_rate, 2),

            # ---- Fraîcheur des plans (ISO 22301 : revue/test périodiques) ----
            'stale_bcp_count': len(stale_bcp_ids),
            'stale_bcp_ids': stale_bcp_ids,
            'stale_drp_count': len(stale_drp_ids),
            'stale_drp_ids': stale_drp_ids,

            # ---- Actions correctives issues des exercices (ISO 22398) ----
            'open_corrective_actions_count': len(open_corrective_actions),
            'overdue_corrective_actions_count': len(overdue_corrective_actions),
            'open_corrective_action_ids': open_corrective_actions.ids,

            # ---- Qualité des données BIA ----
            'rto_exceeds_mtd_count': len(inconsistent_activities),
            'rto_exceeds_mtd_ids': inconsistent_activities.ids,
        }

    @api.depends()
    def _compute_dashboard(self):
        """Champs conservés pour compatibilité avec l'ancienne vue formulaire
        (list/form/pivot/graph). Ils reprennent désormais tous la même
        définition que get_resilience_kpis, au lieu d'une formule locale
        distincte."""
        kpis = self.get_resilience_kpis()
        for rec in self:
            rec.avg_rto = kpis['avg_rto']
            rec.avg_rpo = kpis['avg_rpo']
            rec.avg_mtd = kpis['avg_mtd']
            rec.exercise_count = kpis['exercise_count']
            rec.bcp_coverage = kpis['bcp_coverage']
            rec.drp_coverage = kpis['drp_coverage']
