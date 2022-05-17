import type {RowFilterType} from './row-filter-type';

/**
 * Generated from ai.giskard.domain.ml.table.Filter
 */
export interface Filter {
    maxLabelThreshold: number;
    maxThreshold: number;
    minLabelThreshold: number;
    minThreshold: number;
    predictedLabel: string[];
    regressionUnit: string;
    rowFilter: RowFilterType;
    targetLabel: string[];
    thresholdLabel: string;
}