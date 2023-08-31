import {defineStore} from "pinia";
import {api} from "@/api";
import {ApiKeyDTO} from "@/generated-sources";

interface ApiKeyState {
    apiKeys: ApiKeyDTO[],
}

export const useApiKeyStore = defineStore('apiKeys', {
    state: (): ApiKeyState => ({
        apiKeys: [],
    }),
    getters: {
        getFirstApiKey(state: ApiKeyState) {
            if (state.apiKeys.length) {
                return state.apiKeys[0].key;
            }
            return null;
        }
    },
    actions: {
        async getAll() {
            this.apiKeys = await api.getApiKeys();
        },
        async delete(id: string) {
            this.apiKeys = await api.deleteApiKey(id);
        },
        async create() {
            this.apiKeys = await api.createApiKey();
        }
    }
});

