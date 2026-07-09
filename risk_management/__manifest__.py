{
    'name': 'Risk Management',
    'version': '19.0.1.0.0',
    'category': 'Risk Management',
    'summary': 'Enterprise Risk Management',
    'author': 'Your Company',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'hr',
        'calendar',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/sequence.xml',
        'data/risk_scale_data.xml',
        'data/risk_tag_data.xml',
        'data/cron_data.xml',
        'data/email_template_data.xml',
        'data/risk_categories.xml',
        'data/risk_process_data.xml',
        'data/risk_activity_data.xml',
        'data/risk_risk_data.xml',
        'data/kri_data.xml',
        #'data/employee_data.xml',
        'data/risk_control_data.xml',

        # ============================================================
        # 1. VUES DE BASE (Modèles simples)
        # ============================================================
        'views/risk_category_views.xml',
        'views/risk_macro_process_views.xml',
        'views/risk_process_views.xml',
        'views/risk_activity_views.xml',
        'views/risk_organization_views.xml',
        'views/risk_asset_views.xml',
        'views/risk_cause_views.xml',
        'views/risk_impact_views.xml',
        'views/risk_incident_category_views.xml',
        'views/risk_incident_type_views.xml',
        'views/risk_root_cause_views.xml',

        # ============================================================
        # 2. VUES PRINCIPALES
        # ============================================================
        'views/risk_risk_views.xml',
        'views/risk_control_views.xml',
        'views/risk_control_test_views.xml',
        'views/risk_kri_views.xml',
        'views/risk_kri_measure_views.xml',
        'views/risk_incident_views.xml',
        'views/risk_loss_views.xml',
        'views/risk_corrective_action_views.xml',
        'views/risk_cartography_views.xml',

        # ============================================================
        # 3. VUES AUDIT
        # ============================================================
        'views/risk_audit_views.xml',
        'views/risk_audit_plan_views.xml',
        'views/risk_audit_finding_views.xml',
        'views/risk_audit_recommendation_views.xml',
        'views/risk_audit_action_plan_views.xml',
        'views/risk_audit_scope_views.xml',

        # ============================================================
        # 4. VUES BIA
        # ============================================================
        'views/risk_bia_views.xml',
        'views/risk_bia_activity_views.xml',

        # ============================================================
        # 5. VUES BCP/DRP
        # ============================================================
        'views/risk_bcp_plan_views.xml',
        'views/risk_bcp_resource_views.xml',
        'views/risk_drp_plan_views.xml',
        'views/risk_recovery_site_views.xml',

        # ============================================================
        # 6. VUES CRISIS
        # ============================================================
        'views/risk_crisis_scenario_views.xml',
        'views/risk_crisis_views.xml',
        'views/risk_crisis_committee_meeting_views.xml',
        'views/risk_crisis_dashboard_views.xml',
        'views/risk_crisis_dashboard_line_views.xml',
        'views/risk_crisis_kpi_history_views.xml',
        'views/risk_crisis_heatmap_views.xml',
        'views/risk_crisis_lessons_learned_dashboard_views.xml',
        'views/risk_crisis_regulatory_reporting_views.xml',
        'views/risk_crisis_communication_template_views.xml',
        'views/risk_crisis_contact_directory_views.xml',
        'views/risk_crisis_media_monitoring_views.xml',
        'views/risk_crisis_warroom_views.xml',
        'views/risk_crisis_timeline_views.xml',
        'views/risk_crisis_command_center_views.xml',
        'views/risk_exercise_views.xml',
        'views/risk_exercise_finding_views.xml',

        # ============================================================
        # 7. VUES COMPLIANCE
        # ============================================================
        'views/risk_compliance_framework_views.xml',
        'views/risk_compliance_requirement_views.xml',
        'views/risk_compliance_assessment_views.xml',
        'views/risk_compliance_obligation_views.xml',
        'views/risk_compliance_evidence_views.xml',
        'views/risk_compliance_action_plan_views.xml',
        'views/risk_compliance_scorecard_views.xml',
        'views/risk_compliance_scorecard_line_views.xml',

        # ============================================================
        # 8. VUES DASHBOARD
        # ============================================================
        'views/risk_heatmap_views.xml',
        'views/risk_heatmap_line_views.xml',
        'views/risk_continuity_dashboard_views.xml',
        'views/risk_risk_dashboard_views.xml',
        'views/risk_config_views.xml',
        'views/risk_process_cartography_views.xml',

        # ============================================================
        # 9. VUES GOUVERNANCE (DOIVENT ÊTRE AVANT LES ACTIONS)
        # ============================================================
        'views/risk_tag_views.xml',
        'views/risk_policy_views.xml',
        'views/risk_document_category_views.xml',
        'views/risk_document_views.xml',
        'views/risk_document_version_views.xml',
        'views/risk_document_approval_views.xml',
        'views/risk_document_distribution_views.xml',
        'views/risk_action_plan_views.xml',
        'views/risk_action_task_views.xml',
        'views/risk_kri_compute_wizard_views.xml',

        # ============================================================
        # 10. ACTIONS (RÉFÉRENCENT LES VUES)
        # ============================================================
        'views/grc_actions.xml',

        # ============================================================
        # 11. MENUS (TOUJOURS EN DERNIER)
        # ============================================================
        'views/grc_menu.xml',

        # ============================================================
        # 12. RAPPORTS
        # ============================================================
        'reports/risk_register_report.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'risk_management/static/src/dashboard/grc_dashboard.js',
            'risk_management/static/src/dashboard/grc_dashboard.xml',
            'risk_management/static/src/dashboard/grc_dashboard.scss',
            'risk_management/static/src/js/crisis_command_center.js',
            'risk_management/static/src/xml/crisis_command_center.xml',
            'risk_management/static/src/scss/crisis_command_center.scss',
            'risk_management/static/src/scss/risk_risk_dashboard.scss',
            'risk_management/static/src/js/executive_dashboard_widget.js',
            'risk_management/static/src/xml/executive_dashboard_widget.xml',
            'risk_management/static/src/scss/executive_dashboard_widget.scss',
            'risk_management/static/src/scss/risk_process_cartography_views.scss',
            'risk_management/static/src/scss/risk_process_views.scss',
            'risk_management/static/src/js/risk_heatmap.js',
            'risk_management/static/src/xml/risk_heatmap.xml',
            'risk_management/static/src/scss/risk_heatmap.scss',
            'risk_management/static/src/js/process_dashboard.js',
            'risk_management/static/src/xml/process_dashboard.xml',
            'risk_management/static/src/scss/process_dashboard.scss',
            'risk_management/static/src/scss/risk_risk_views.scss',
            'risk_management/static/src/js/kri_dashboard.js',
            'risk_management/static/src/xml/kri_dashboard.xml',
            'risk_management/static/src/scss/kri_dashboard.scss',
            'risk_management/static/src/js/document_version_widget.js',
        ],
        'web.report_assets_common': [
            'risk_management/static/src/css/report_style.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}