import type {TransformationResultMessageDTO} from './transformation-result-message-dto';

/**
 * Generated from ai.giskard.web.dto.DatasetProcessingResultDTO
 */
export interface DatasetProcessingResultDTO {
    datasetId: string;
    filteredRows: number[];
    modifications: TransformationResultMessageDTO[];
    totalRows: number;
}