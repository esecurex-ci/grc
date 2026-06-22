/** @odoo-module **/

import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";
import {Component, onWillStart, useState} from "@odoo/owl";

export class RiskHeatMap extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");

        // État réactif contenant notre matrice 5x5
        this.state = useState({
            matrix: this.initializeMatrix(),
        });

        onWillStart(async () => {
            await this.fetchRiskData();
        });
    }

    initializeMatrix() {
        // Initialisation de la matrice (Impact de 5 à 1, Probabilité de 1 à 5)
        const matrix = {};
        for (let impact = 5; impact >= 1; impact--) {
            matrix[impact] = {};
            for (let likelihood = 1; likelihood <= 5; likelihood++) {
                matrix[impact][likelihood] = 0;
            }
        }
        return matrix;
    }

    async fetchRiskData() {
        // Paramètres pour le read_group Odoo
        const domain = []; // Ajoutez un domaine ici si nécessaire, ex: [("state", "=", "active")]
        const fields = ["impact", "likelihood"];
        const groupby = ["impact", "likelihood"];

        try {
            // Utilisation de this.orm.call() qui est la méthode la plus sûre
            const result = await this.orm.call(
                "rm.risk.risk", // Le nom exact de votre modèle
                "read_group",   // La méthode Python appelée
                [domain, fields, groupby], // Les arguments positionnels (args)
                { lazy: false } // kwargs : lazy=false permet d'avoir toutes les combinaisons croisées
            );

            const newMatrix = this.initializeMatrix();

            // Odoo renvoie un tableau d'objets. Le nombre d'enregistrements est dans '__count'
            result.forEach(group => {
                const impact = group.impact;
                const likelihood = group.likelihood;
                const count = group.__count || 0;

                if (impact && likelihood && newMatrix[impact]) {
                    newMatrix[impact][likelihood] += count;
                }
            });

            this.state.matrix = newMatrix;

        } catch (error) {
            console.error("Erreur lors de la récupération des données de la Heat Map :", error);
        }
    }

    // Détermine la classe CSS de couleur basée sur la capture d'écran
    getCellClass(impact, likelihood) {
        const score = impact * likelihood;

        if (score >= 20 || (impact === 5)) return 'hm-red';
        if (score >= 12 || (impact === 4 && likelihood >= 2)) return 'hm-orange';
        if (score >= 6 || (impact === 3 && likelihood >= 2)) return 'hm-yellow';
        if (score >= 3 || (impact === 2 && likelihood >= 2)) return 'hm-green';
        return 'hm-blue';
    }

    // Permet d'ouvrir la liste des risques en cliquant sur une case
    openRiskList(impact, likelihood) {
        this.action.doAction({
            type: "ir.actions.act_window",
            name: `Risques (Impact: ${impact}, Probabilité: ${likelihood})`,
            res_model: "risk.risk",
            views: [[false, "list"], [false, "form"]], // Utilisation stricte de 'list' pour la V19
            //domain: [["impact", "=", impact], ["likelihood", "=", likelihood]],
            domain: [["impact_value", "=", impact], ["probability_value", "=", likelihood]],
            target: "current",
        });
    }
}

RiskHeatMap.template = "rm_risk.RiskHeatMapTemplate";

// Enregistrement du composant en tant qu'action client
registry.category("actions").add("rm_risk_heatmap_client_action", RiskHeatMap);