/** @odoo-module **/

import { Component,onWillStart,useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CrisisCommandCenter extends Component {

    setup() {

        this.orm = useService("orm");

        this.state = useState({
            data: {}
        });

        onWillStart(async () => {

            this.state.data =
                await this.orm.call(
                    "risk.crisis.command.center",
                    "get_dashboard_data",
                    []
                );
        });
    }
}

CrisisCommandCenter.template =
    "risk_management.CrisisCommandCenter";

registry.category("actions").add(
    "risk_crisis_command_center",
    CrisisCommandCenter
);