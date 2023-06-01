import {CallableDTO, CatalogDTO} from '@/generated-sources';
import {defineStore} from 'pinia';
import {api} from '@/api';
import {chain} from "lodash";

interface State {
    catalog: CatalogDTO | null
}


function latestVersions<E extends CallableDTO>(data?: Array<E>): Array<E> {
    return chain(data ?? [])
        .groupBy(func => `${func.module}.${func.name}`)
        .mapValues(functions => chain(functions)
            .maxBy(func => func.version ?? 1)
            .value())
        .values()
        .sortBy('name')
        .value() as Array<E>
}

export const useCatalogStore = defineStore('catalog', {
    state: (): State => ({
        catalog: null
    }),
    getters: {
        testFunctions(state: State) {
            return latestVersions(state.catalog?.tests)
        },
        sliceFunctions(state: State) {
            return latestVersions(state.catalog?.slices)
        }
    },
    actions: {
        async loadCatalog(projectId: number) {
            this.catalog = null;
            this.catalog = await api.getCatalog(projectId);
        },
    }
});
