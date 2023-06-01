import type {DatasetDescribeColumnDTO} from './dataset-describe-column-dto';

/**
 * Generated from ai.giskard.web.dto.TransformationResultDTO
 */
export interface TransformationResultDTO {
    describeColumns: DatasetDescribeColumnDTO[];
    modifiedRow: number;
    totalRow: number;
}