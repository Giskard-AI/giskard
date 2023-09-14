import {InspectionCreateDTO, InspectionDTO, ParameterizedCallableDTO, RowFilterType} from '@/generated-sources';
import {defineStore} from 'pinia';
import {api} from '@/api';

interface FilterType {
    label: string;
    value: RowFilterType;
    disabled?: boolean;
    description?: string;
}

interface State {
    projectId: number | null;
    debuggingSessions: Array<InspectionDTO>;
    currentDebuggingSessionId: number | null;
    selectedSlicingFunction: Partial<ParameterizedCallableDTO>;
    selectedFilter: FilterType | null
}

export const useDebuggingSessionsStore = defineStore('debuggingSessions', {
    state: (): State => ({
        projectId: null,
        debuggingSessions: [],
        currentDebuggingSessionId: null,
        selectedSlicingFunction: {
            uuid: undefined,
            params: [],
            type: 'SLICING'
        },
        selectedFilter: null
    }),
    getters: {},
    actions: {
        async reload() {
            if (this.projectId !== null) {
                await this.loadDebuggingSessions(this.projectId);
            }
        },
        clear() {
            this.selectedSlicingFunction = {
                uuid: undefined,
                params: [],
                type: 'SLICING'
            }
        },
        async loadDebuggingSessions(projectId: number) {
            if (this.projectId !== projectId) {
                this.projectId = projectId;
                this.currentDebuggingSessionId = null;
            }
            this.debuggingSessions = await api.getProjectInspections(this.projectId);
        },
        async createDebuggingSession(inspection: InspectionCreateDTO) {
            const newDebuggingSession = await api.prepareInspection(inspection);
            await this.reload();
            return newDebuggingSession;
        },
        async deleteDebuggingSession(inspectionId: number) {
            await api.deleteInspection(inspectionId);
            if (this.currentDebuggingSessionId === inspectionId) {
                this.currentDebuggingSessionId = null;
            }
            await this.reload();
        },
        async updateDebuggingSessionName(inspectionId: number, inspection: InspectionCreateDTO) {
            await api.updateInspectionName(inspectionId, inspection);
            await this.reload();
        },
        setCurrentDebuggingSessionId(inspectionId: number | null) {
            this.currentDebuggingSessionId = inspectionId;
            this.clear();
        },
        setCurrentSlicingFunctionUuid(uuid: string) {
            this.selectedSlicingFunction = {
                uuid: uuid,
                params: [],
                type: 'SLICING'
            };
        },
        setSelectedFilter(filter: FilterType | null) {
            this.selectedFilter = filter;
        }
    },
});
