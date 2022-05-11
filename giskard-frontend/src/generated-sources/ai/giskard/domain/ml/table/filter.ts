import type {RowFilterType} from './row-filter-type';

/**
 * Generated from ai.giskard.domain.ml.table.Filter
 */
export interface Filter {
    maxThreshold: number;
    minThreshold: number;
    predictedLabel: string;
    targetLabel: string;
    rowFilter: RowFilterType;
}