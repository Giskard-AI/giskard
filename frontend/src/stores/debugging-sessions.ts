import { InspectionDTO, InspectionCreateDTO } from '@/generated-sources';
import { defineStore } from 'pinia';
import { api } from '@/api';

interface State {
  projectId: number | null;
  debuggingSessions: Array<InspectionDTO>;
}

export const useDebuggingSessionsStore = defineStore('debuggingSessions', {
  state: (): State => ({
    projectId: null,
    debuggingSessions: [],
  }),
  getters: {},
  actions: {
    async reload() {
      if (this.projectId !== null) {
        await this.loadDebuggingSessions(this.projectId);
      }
    },
    async loadDebuggingSessions(projectId: number) {
      this.projectId = projectId;
      this.debuggingSessions = await api.getProjectInspections(this.projectId);
    },
    async createDebuggingSession(inspection: InspectionCreateDTO) {
      const newDebuggingSession = await api.prepareInspection(inspection);
      await this.reload();
      return newDebuggingSession;
    },
    async deleteDebuggingSession(inspectionId: number) {
      await api.deleteInspection(inspectionId);
      await this.reload();
    },
    async updateDebuggingSessionName(inspectionId: number, inspection: InspectionCreateDTO) {
      await api.updateInspectionName(inspectionId, inspection);
      await this.reload();
    },
  },
});
