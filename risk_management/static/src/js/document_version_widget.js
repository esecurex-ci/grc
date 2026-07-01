/** @odoo-module **/

console.log("📦 Fichier document_version_widget.js chargé !");

import { Component, useState, onWillStart, markup } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

console.log("📦 Imports OK !");

export class DocumentVersionWidget extends Component {
    static template = "risk_management.document_version_widget";
    static props = {
        record: { type: Object },
        resId: { type: Number, optional: true },
        resModel: { type: String, optional: true },
    };

    setup() {
        console.log("📦 Setup DocumentVersionWidget !");
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");

        this.state = useState({
            loading: true,
            versions: [],
            currentVersion: null,
            document: null,
            isCreating: false,
            uploading: false,
            progress: 0,
            selectedFile: null,
            changelog: '',
            versionType: 'minor',
            effectiveDate: new Date().toISOString().split('T')[0],
        });

        onWillStart(async () => {
            console.log("📦 onWillStart !");
            await this.loadVersions();
        });
    }

    // ============================================================
    // CHARGEMENT DES VERSIONS
    // ============================================================
    async loadVersions() {
        console.log("📦 loadVersions !");
        try {
            const docId = this.props.record?.resId || this.props.resId;
            if (!docId) {
                console.warn("📦 Aucun ID de document trouvé");
                return;
            }

            // Charger le document
            const document = await this.orm.searchRead(
                'risk.document',
                [['id', '=', docId]],
                ['id', 'name', 'code', 'version_label', 'version_major', 'version_minor', 'current_version_id'],
                { limit: 1 }
            );

            if (document && document.length > 0) {
                this.state.document = document[0];
            }

            // Charger les versions
            const versions = await this.orm.searchRead(
                'risk.document.version',
                [['document_id', '=', docId]],
                [
                    'id', 'version_label', 'version_major', 'version_minor',
                    'state', 'filename', 'file_size', 'author_id', 'reviewer_id',
                    'approver_id', 'creation_date', 'approval_date', 'effective_date',
                    'changelog', 'summary', 'is_current', 'is_obsolete',
                    'attachment_id'
                ],
                { order: 'version_major desc, version_minor desc' }
            );

            this.state.versions = versions;

            // Trouver la version actuelle
            const current = versions.find(v => v.is_current === true);
            this.state.currentVersion = current || null;

            console.log("📦 Versions chargées :", this.state.versions);
            console.log("📦 Version actuelle :", this.state.currentVersion);

        } catch (error) {
            console.error("📦 Erreur lors du chargement des versions :", error);
            this.notification.add("Erreur lors du chargement des versions", { type: 'danger' });
            this.loadTestData();
        } finally {
            this.state.loading = false;
        }
    }

    // ============================================================
    // DONNÉES DE TEST
    // ============================================================
    loadTestData() {
        this.state.versions = [
            {
                id: 1,
                version_label: 'v2.1',
                version_major: 2,
                version_minor: 1,
                state: 'published',
                filename: 'politique_securite_v2.1.pdf',
                file_size: 245,
                author_id: ['', 'Jean Dupont'],
                creation_date: '2024-01-15',
                approval_date: '2024-01-20',
                effective_date: '2024-02-01',
                changelog: 'Mise à jour des règles de sécurité',
                is_current: true,
                is_obsolete: false,
            },
            {
                id: 2,
                version_label: 'v2.0',
                version_major: 2,
                version_minor: 0,
                state: 'archived',
                filename: 'politique_securite_v2.0.pdf',
                file_size: 230,
                author_id: ['', 'Jean Dupont'],
                creation_date: '2023-12-01',
                approval_date: '2023-12-10',
                effective_date: '2024-01-01',
                changelog: 'Version majeure - Refonte complète',
                is_current: false,
                is_obsolete: true,
            },
            {
                id: 3,
                version_label: 'v1.5',
                version_major: 1,
                version_minor: 5,
                state: 'archived',
                filename: 'politique_securite_v1.5.pdf',
                file_size: 180,
                author_id: ['', 'Marie Martin'],
                creation_date: '2023-09-15',
                approval_date: '2023-09-25',
                effective_date: '2023-10-01',
                changelog: 'Corrections mineures',
                is_current: false,
                is_obsolete: true,
            },
        ];
        this.state.currentVersion = this.state.versions[0];
        this.state.document = {
            id: 1,
            name: 'Politique de Sécurité',
            code: 'POL-SEC-001',
            version_label: 'v2.1',
        };
        this.state.loading = false;
    }

    // ============================================================
    // MÉTHODES D'ACTION
    // ============================================================

    async createVersion() {
        console.log("📦 createVersion !");
        if (!this.state.selectedFile) {
            this.notification.add("Veuillez sélectionner un fichier", { type: 'warning' });
            return;
        }

        this.state.uploading = true;
        this.state.progress = 0;

        try {
            const reader = new FileReader();
            reader.onload = async (e) => {
                const content = e.target.result.split(',')[1];
                const docId = this.props.record?.resId || this.props.resId;

                // Créer la pièce jointe
                const attachmentId = await this.orm.call(
                    'ir.attachment',
                    'create',
                    [{
                        name: this.state.selectedFile.name,
                        datas: content,
                        datas_fname: this.state.selectedFile.name,
                        res_model: 'risk.document',
                        res_id: docId,
                    }],
                    {}
                );

                // Créer la version
                const versionData = {
                    document_id: docId,
                    attachment_id: attachmentId,
                    changelog: this.state.changelog,
                    version_type: this.state.versionType,
                    effective_date: this.state.effectiveDate,
                    author_id: this.env.user.employee_id ? this.env.user.employee_id[0] : false,
                };

                await this.orm.call('risk.document.version', 'create', [versionData], {});

                this.notification.add(
                    `Version "${this.state.selectedFile.name}" créée avec succès !`,
                    { type: 'success' }
                );

                // Réinitialiser le formulaire
                this.state.selectedFile = null;
                this.state.changelog = '';
                this.state.versionType = 'minor';
                this.state.isCreating = false;
                this.state.progress = 0;

                // Recharger les versions
                await this.loadVersions();

            };
            reader.readAsDataURL(this.state.selectedFile);

        } catch (error) {
            console.error("📦 Erreur lors de la création de la version :", error);
            this.notification.add("Erreur lors de la création de la version", { type: 'danger' });
        } finally {
            this.state.uploading = false;
            this.state.progress = 0;
        }
    }

    setCurrentVersion(versionId) {
        console.log("📦 setCurrentVersion :", versionId);
        const version = this.state.versions.find(v => v.id === versionId);
        if (!version) return;

        this.dialog.add({
            title: '⭐ Définir comme version actuelle',
            body: markup(`
                <p>Êtes-vous sûr de vouloir définir la version <strong>${version.version_label}</strong> comme version actuelle du document ?</p>
                <p class="text-muted">Cette version deviendra la référence pour le document.</p>
            `),
            confirmLabel: 'Confirmer',
            cancelLabel: 'Annuler',
            confirm: async () => {
                try {
                    const docId = this.props.record?.resId || this.props.resId;
                    await this.orm.call(
                        'risk.document.version',
                        'action_set_current',
                        [[versionId]],
                        {}
                    );
                    this.notification.add(
                        `Version ${version.version_label} définie comme actuelle`,
                        { type: 'success' }
                    );
                    await this.loadVersions();
                } catch (error) {
                    console.error("📦 Erreur :", error);
                    this.notification.add("Erreur lors de la mise à jour", { type: 'danger' });
                }
            }
        });
    }

    downloadVersion(versionId) {
        console.log("📦 downloadVersion :", versionId);
        const version = this.state.versions.find(v => v.id === versionId);
        if (!version) return;

        // Utiliser l'action Odoo pour télécharger
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Télécharger',
            res_model: 'ir.attachment',
            view_mode: 'form',
            res_id: version.attachment_id[0],
            target: 'new',
            context: { 'default_res_model': 'ir.attachment' },
        });
    }

    deleteVersion(versionId) {
        console.log("📦 deleteVersion :", versionId);
        const version = this.state.versions.find(v => v.id === versionId);
        if (!version) return;

        this.dialog.add({
            title: '🗑️ Supprimer la version',
            body: markup(`
                <p>Êtes-vous sûr de vouloir supprimer la version <strong>${version.version_label}</strong> ?</p>
                <p class="text-danger">Cette action est irréversible.</p>
            `),
            confirmLabel: 'Supprimer',
            cancelLabel: 'Annuler',
            confirm: async () => {
                try {
                    await this.orm.call(
                        'risk.document.version',
                        'unlink',
                        [[versionId]],
                        {}
                    );
                    this.notification.add(
                        `Version ${version.version_label} supprimée`,
                        { type: 'success' }
                    );
                    await this.loadVersions();
                } catch (error) {
                    console.error("📦 Erreur :", error);
                    this.notification.add("Erreur lors de la suppression", { type: 'danger' });
                }
            }
        });
    }

    // ============================================================
    // FONCTIONS UTILITAIRES
    // ============================================================

    getStatusBadge(state) {
        const badges = {
            'draft': 'badge-secondary',
            'review': 'badge-warning',
            'approved': 'badge-info',
            'published': 'badge-success',
            'archived': 'badge-danger',
        };
        return badges[state] || 'badge-secondary';
    }

    getStatusLabel(state) {
        const labels = {
            'draft': '📝 Brouillon',
            'review': '🔍 En relecture',
            'approved': '✅ Approuvé',
            'published': '📤 Publié',
            'archived': '📦 Archivé',
        };
        return labels[state] || state;
    }

    getVersionTypeLabel(type) {
        const labels = {
            'initial': '🎯 Initiale',
            'major': '📈 Majeure',
            'minor': '📝 Mineure',
            'correction': '🔧 Correction',
            'review': '📋 Révision',
            'archived': '📦 Archivée',
        };
        return labels[type] || type;
    }

    getFileIcon(filename) {
        const ext = filename?.split('.').pop()?.toLowerCase() || '';
        const icons = {
            'pdf': 'fa-file-pdf-o text-danger',
            'doc': 'fa-file-word-o text-primary',
            'docx': 'fa-file-word-o text-primary',
            'xls': 'fa-file-excel-o text-success',
            'xlsx': 'fa-file-excel-o text-success',
            'ppt': 'fa-file-powerpoint-o text-warning',
            'pptx': 'fa-file-powerpoint-o text-warning',
            'txt': 'fa-file-text-o',
            'zip': 'fa-file-archive-o',
            'rar': 'fa-file-archive-o',
            'jpg': 'fa-file-image-o',
            'png': 'fa-file-image-o',
        };
        return icons[ext] || 'fa-file-o';
    }

    formatDate(dateStr) {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString('fr-FR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    }

    onFileSelected(event) {
        const file = event.target.files[0];
        if (file) {
            this.state.selectedFile = file;
            this.state.progress = 0;
        }
    }

    toggleCreateForm() {
        this.state.isCreating = !this.state.isCreating;
        if (!this.state.isCreating) {
            this.state.selectedFile = null;
            this.state.changelog = '';
            this.state.versionType = 'minor';
        }
    }

    onDragOver(event) {
        event.preventDefault();
        event.stopPropagation();
        this.state.dragover = true;
    }

    onDragLeave(event) {
        event.preventDefault();
        event.stopPropagation();
        this.state.dragover = false;
    }

    onDrop(event) {
        event.preventDefault();
        event.stopPropagation();
        this.state.dragover = false;
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.state.selectedFile = files[0];
            this.state.progress = 0;
        }
    }
}

console.log("📦 DocumentVersionWidget exporté !");

// ============================================================
// ENREGISTREMENT
// ============================================================
registry.category('components').add('risk_management.document_version_widget', DocumentVersionWidget);

console.log("📦 Widget document_version_widget enregistré !");