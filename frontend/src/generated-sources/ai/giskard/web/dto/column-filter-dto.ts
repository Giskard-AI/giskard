import type {ColumnType} from './../../domain/column-type';
import type {NoCodeSlicingType} from './no-code-slicing-type';

/**
 * Generated from ai.giskard.web.dto.ColumnFilterDTO
 */
export interface ColumnFilterDTO {
    column: string;
    columnType: ColumnType;
    slicingType: NoCodeSlicingType;
    value?: string | null;
}