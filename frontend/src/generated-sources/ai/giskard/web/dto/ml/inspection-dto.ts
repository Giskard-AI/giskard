import type {DatasetDTO} from './dataset-dto';
import type {ModelDTO} from './model-dto';

/**
 * Generated from ai.giskard.web.dto.ml.InspectionDTO
 */
export interface InspectionDTO {
    createdDate: any /* TODO: Missing translation of java.time.Instant */;
    dataset: DatasetDTO;
    id: number;
    model: ModelDTO;
    name: string;
    sample: boolean;
}