import { InspectionDTO, InspectionCreateDTO } from '@/generated-sources';
import { defineStore } from 'pinia';
import { api } from '@/api';

interface State {
  projectId: number | null;
  debuggingSessions: Array<InspectionDTO>;
  currentDebuggingSessionId: number | null;
}

export const useDebuggingSessionsStore = defineStore('debuggingSessions', {
  state: (): State => ({
    projectId: null,
    debuggingSessions: [],
    currentDebuggingSessionId: null,
  }),
  getters: {},
  actions: {
    async reload() {
      if (this.projectId !== null) {
        await this.loadDebuggingSessions(this.projectId);
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
    },
  },
});
