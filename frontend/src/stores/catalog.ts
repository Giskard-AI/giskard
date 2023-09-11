import { ColumnType, DatasetDTO } from '@/generated-sources';
import { defineStore } from 'pinia';
import { chain } from 'lodash';
import { getColumnType } from '@/utils/column-type-utils';
import { openapi } from '@/api-v2';
import {
    CatalogDTO,
    ComparisonClauseDTO,
    SlicingFunctionDTO,
    TestFunctionDTO,
    TransformationFunctionDTO
} from '@/generated/client';

type DatasetProcessFunctionDTO = TransformationFunctionDTO & SlicingFunctionDTO
type CallableDTO = DatasetProcessFunctionDTO & TestFunctionDTO

interface State {
    catalog: CatalogDTO | null;
}


function latestVersions<E extends CallableDTO>(data?: Array<E>): Array<E> {
    return chain(data ?? [])
      .groupBy(func => func.displayName)
        .mapValues(functions => chain(functions)
            .maxBy(func => func.version ?? 1)
            .value())
        .values()
        .sortBy('name')
        .value() as Array<E>
}

function keyByUuid<E extends CallableDTO>(data?: Array<E>): { [uuid: string]: E } {
    return chain(data ?? []).keyBy('uuid').value()
}

function groupByColumnType<E extends DatasetProcessFunctionDTO>(data?: Array<E>) {
    return chain(data ?? [])
      .filter(d => d.cellLevel! && getColumnType(d.columnType) !== null)
        .groupBy(d => getColumnType(d.columnType))
        .value()
}

export const useCatalogStore = defineStore('catalog', {
    state: (): State => ({
        catalog: null
    }),
    getters: {
        testFunctions(state: State) {
            return latestVersions(state.catalog?.tests)
        },
        testFunctionsByUuid(state: State) {
            return keyByUuid(state.catalog?.tests)
        },
        slicingFunctions(state: State) {
            return latestVersions(state.catalog?.slices)
        },
        slicingFunctionsByUuid(state: State) {
            return keyByUuid(state.catalog?.slices)
        },
        transformationFunctions(state: State) {
            return latestVersions(state.catalog?.transformations)
        },
        transformationFunctionsByUuid(state: State) {
            return keyByUuid(state.catalog?.transformations)
        },
        transformationFunctionsByColumnType(state: State) {
            return groupByColumnType(latestVersions(state.catalog?.transformations))
        },
    },
    actions: {
        async loadCatalog(projectId: number) {
            this.catalog = await openapi.catalog.getCatalog({ projectId });
        },
        async createSlicingFunction(projectKey: string, dataset: DatasetDTO, clauses: Array<ComparisonClauseDTO & {
            columnType: ColumnType
        }>) {
            const slicingFunction = await openapi.slicingFunction.createNoCodeSlicingFunction({
                projectKey,
                comparisonClauseDTO: clauses.map(c => {
                    const { columnType, ...clause } = c;
                    return {
                        ...clause,
                        columnDtype: dataset.columnDtypes[clause.columnName]
                    };
                })
            });

            this.catalog!.slices!.push(slicingFunction);
            return slicingFunction;
        }
    }
});
