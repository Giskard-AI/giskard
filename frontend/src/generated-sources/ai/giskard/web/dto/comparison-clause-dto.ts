import type {ComparisonType} from './comparison-type';

/**
 * Generated from ai.giskard.web.dto.ComparisonClauseDTO
 */
export interface ComparisonClauseDTO {
    columnDtype: string;
    columnName: string;
    comparisonType: ComparisonType;
    value?: string | null;
}