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
            open_incidents: 0,
            compliance_rate: 0,

            top_risks: []

        });

        onWillStart(async () => {

            await this.loadDashboard();

        });

    }

    async loadDashboard() {

        const dashboard =
            await this.orm.searchRead(

                "risk.executive.dashboard.snapshot",

                [],

                [
                    "overall_score",
                    "total_risks",
                    "critical_risks",
                    "open_incidents",
                    "compliance_rate"
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

        this.state.top_risks =
            await this.orm.searchRead(

                "risk.risk",

                [
                    ["residual_level", "=", "critical"]
                ],

                [
                    "name",
                    "residual_score"
                ],

                {
                    limit: 10
                }

            );

    }

    openRisks() {

        this.action.doAction({

            type: "ir.actions.act_window",

            name: "Risks",

            res_model: "risk.risk",

            views: [[false, "list"], [false, "form"]]

        });

    }

}

GrcDashboard.template =
    "risk_management.GrcDashboard";

registry.category("actions").add(
    "grc_dashboard",
    GrcDashboard
);