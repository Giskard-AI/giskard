import type {ColumnFilterDTO} from './column-filter-dto';
import type {Filter} from './../../domain/ml/table/filter';

/**
 * Generated from ai.giskard.web.dto.RowFilterDTO
 */
export interface RowFilterDTO {
    columnFilters?: ColumnFilterDTO[] | null;
    filter?: Filter | null;
    removeRows?: number[] | null;
}