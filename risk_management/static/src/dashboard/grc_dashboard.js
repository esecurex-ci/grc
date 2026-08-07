/** @odoo-module **/

import { Component, onWillStart, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";

import { useService } from "@web/core/utils/hooks";

export class GrcDashboard extends Component {

    setup() {

        this.orm = useService("orm");
        this.action = useService("action");

        this.state = useState({

            overall_score: 0,
            total_risks: 0,
            critical_risks: 0,
            high_risks: 0,
            open_incidents: 0,
            compliance_rate: 0,

            // ---- Scores GRC par domaine ----
            risk_score: 0,
            compliance_score: 0,
            audit_score: 0,
            resilience_score: 0,
            cyber_score: 0,

            // ---- Incidents & Pertes ----
            total_incidents: 0,
            critical_incidents: 0,
            operational_losses: 0,

            // ---- Audit ----
            total_findings: 0,
            open_findings: 0,
            critical_findings: 0,
            overdue_audit_actions: 0,

            // ---- Conformité ----
            non_compliant_requirements: 0,
            overdue_compliance_actions: 0,

            // ---- Résilience (BCM/DRP) ----
            bcp_coverage_rate: 0,
            drp_coverage_rate: 0,
            exercise_success_rate: 0,

            // ---- Gestion de Crise ----
            crisis_count: 0,
            average_detection_time: 0,
            average_recovery_time: 0,
            average_closure_time: 0,

            // ---- Contrôles & KRI ----
            control_score: 0,
            total_controls: 0,
            ineffective_controls: 0,
            active_kri_alerts: 0,
            kri_over_appetite_count: 0,

            // ---- Gouvernance ----
            total_documents: 0,
            documents_review_overdue: 0,
            expired_documents: 0,
            policies_review_overdue: 0,

            // ---- Reporting ----
            total_regulatory_reports: 0,
            pending_regulatory_reports: 0,
            total_board_reports: 0,

        });

        onWillStart(async () => {

            await this.loadDashboard();

        });

    }

    async loadDashboard() {

        // Le Cockpit dépendait d'un snapshot jamais généré automatiquement
        // (KPI figés à zéro). On s'assure qu'un snapshot du jour existe
        // avant de le charger, sans action manuelle de l'utilisateur.
        try {
            await this.orm.call(
                "risk.metric.engine",
                "action_ensure_dashboard_snapshot",
                [[]]
            );
        } catch (error) {
            console.error("🏛️ Erreur génération snapshot GRC :", error);
        }

        const dashboard =
            await this.orm.searchRead(

                "risk.executive.dashboard.snapshot",

                [],

                [
                    "overall_score",
                    "total_risks",
                    "critical_risks",
                    "high_risks",
                    "open_incidents",
                    "compliance_rate",
                    // Scores GRC par domaine
                    "risk_score",
                    "compliance_score",
                    "audit_score",
                    "resilience_score",
                    "cyber_score",
                    // Incidents & Pertes
                    "total_incidents",
                    "critical_incidents",
                    "operational_losses",
                    // Audit
                    "total_findings",
                    "open_findings",
                    "critical_findings",
                    "overdue_audit_actions",
                    // Conformité
                    "non_compliant_requirements",
                    "overdue_compliance_actions",
                    // Résilience (BCM/DRP)
                    "bcp_coverage_rate",
                    "drp_coverage_rate",
                    "exercise_success_rate",
                    // Gestion de Crise
                    "crisis_count",
                    "average_detection_time",
                    "average_recovery_time",
                    "average_closure_time",
                    // Contrôles & KRI
                    "control_score",
                    "total_controls",
                    "ineffective_controls",
                    "active_kri_alerts",
                    "kri_over_appetite_count",
                    // Gouvernance
                    "total_documents",
                    "documents_review_overdue",
                    "expired_documents",
                    "policies_review_overdue",
                    // Reporting
                    "total_regulatory_reports",
                    "pending_regulatory_reports",
                    "total_board_reports"
                ],

                {
                    limit: 1,
                    order: "snapshot_date desc"
                }

            );

        if (dashboard.length) {

            Object.assign(
                this.state,
                dashboard[0]
            );
        }

    }

    // ============================================================
    // ACTIONS / NAVIGATION
    // ------------------------------------------------------------
    // Déclarées en propriétés de classe à fonction fléchée pour que
    // "this" reste bien lié au composant lorsqu'elles sont appelées
    // depuis un t-on-click du template (même convention que sur les
    // autres tableaux de bord du module).
    // ============================================================
    openRisks = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Risques",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openHighResidualRisks = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Risques à niveau résiduel élevé",
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]],
            domain: [["residual_level", "=", "high"]],
            target: "current",
        });
    }

    openIncidents = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Incidents",
            res_model: "risk.incident",
            views: [[false, "list"], [false, "form"]],
            domain: [["status", "!=", "closed"]],
            target: "current",
        });
    }

    openAuditFindings = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Constats d'audit ouverts",
            res_model: "risk.audit.finding",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "!=", "closed"]],
            target: "current",
        });
    }

    openComplianceAssessments = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Évaluations de conformité",
            res_model: "risk.compliance.assessment",
            views: [[false, "list"], [false, "form"]],
            domain: [["compliance_level", "=", "non_compliant"]],
            target: "current",
        });
    }

    openBcpPlans = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Plans de continuité (BCP/DRP)",
            res_model: "risk.bcp.plan",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openCrises = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Crises",
            res_model: "risk.crisis",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openAllControls = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Contrôles",
            res_model: "risk.control",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openIneffectiveControls = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Contrôles peu efficaces",
            res_model: "risk.control",
            views: [[false, "list"], [false, "form"]],
            domain: [["effectiveness", "=", "low"]],
            target: "current",
        });
    }

    openKriAlerts = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Alertes KRI actives",
            res_model: "risk.kri.alert",
            views: [[false, "list"], [false, "form"]],
            domain: [["resolved", "=", false]],
            target: "current",
        });
    }

    openKriOverAppetite = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "KRI hors appétit",
            res_model: "risk.kri",
            views: [[false, "list"], [false, "form"]],
            domain: [["over_appetite", "=", true]],
            target: "current",
        });
    }

    openAllDocuments = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Documents de gouvernance",
            res_model: "risk.document",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openDocuments = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Révisions de documents en retard",
            res_model: "risk.document",
            views: [[false, "list"], [false, "form"]],
            domain: [["review_status", "=", "overdue"]],
            target: "current",
        });
    }

    openExpiredDocuments = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Documents expirés",
            res_model: "risk.document",
            views: [[false, "list"], [false, "form"]],
            domain: [["expired", "=", true]],
            target: "current",
        });
    }

    openPolicies = () => {
        const today = new Date().toISOString().slice(0, 10);
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Politiques à réviser",
            res_model: "risk.policy",
            views: [[false, "list"], [false, "form"]],
            domain: [["next_review_date", "<", today], ["state", "!=", "archived"]],
            target: "current",
        });
    }

    openRegulatoryReports = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Rapports réglementaires",
            res_model: "risk.regulatory.report",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

    openPendingRegulatoryReports = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Rapports réglementaires en attente",
            res_model: "risk.regulatory.report",
            views: [[false, "list"], [false, "form"]],
            domain: [["state", "=", "draft"]],
            target: "current",
        });
    }

    openBoardReports = () => {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "Rapports au conseil",
            res_model: "risk.board.report",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        });
    }

}

GrcDashboard.template =
    "risk_management.GrcDashboard";

registry.category("actions").add(
    "grc_dashboard",
    GrcDashboard
);