import type {TransformationResultMessageDTO} from './transformation-result-message-dto';

/**
 * Generated from ai.giskard.web.dto.TransformationResultDTO
 */
export interface TransformationResultDTO {
    datasetId: string;
    modifications: TransformationResultMessageDTO[];
    totalRows: number;
}