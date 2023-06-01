import type {RowFilterType} from './row-filter-type';

/**
 * Generated from ai.giskard.domain.ml.table.Filter
 */
export interface Filter {
    inspectionId: number;
    maxDiffThreshold?: number | null;
    maxLabelThreshold?: number | null;
    maxThreshold?: number | null;
    minDiffThreshold?: number | null;
    minLabelThreshold?: number | null;
    minThreshold?: number | null;
    predictedLabel?: string[] | null;
    regressionUnit?: string | null;
    targetLabel?: string[] | null;
    thresholdLabel?: string | null;
    type: RowFilterType;
}