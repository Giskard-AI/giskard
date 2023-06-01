import type {DatasetDescribeColumnDTO} from './dataset-describe-column-dto';

/**
 * Generated from ai.giskard.web.dto.SlicingResultDTO
 */
export interface SlicingResultDTO {
    describeColumns: DatasetDescribeColumnDTO[];
    filteredRow: number;
    totalRow: number;
}