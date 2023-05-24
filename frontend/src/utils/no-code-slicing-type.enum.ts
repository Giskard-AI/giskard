import {ColumnType} from "@/generated-sources";

export enum NoCodeSlicingType {
    IS = 'IS',
    IS_NOT = 'IS_NOT',
    CONTAINS = 'CONTAINS',
    DOES_NOT_CONTAINS = 'DOES_NOT_CONTAINS',
    STARTS_WITH = 'STARTS_WITH',
    ENDS_WITH = 'ENDS_WITH',
    IS_EMPTY = 'IS_EMPTY',
    IS_NOT_EMPTY = 'IS_NOT_EMPTY'
}

export interface NoCodeFilter {
    column: string,
    slicingType: NoCodeSlicingType,
    value?: string,
    columnType: ColumnType
}
