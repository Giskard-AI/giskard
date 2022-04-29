import type {DatasetDTO} from './dataset-dto';
import type {ModelDTO} from './model-dto';

/**
 * Generated from ai.giskard.service.dto.ml.TestSuiteDTO
 */
export interface TestSuiteDTO {
    id: number;
    model: ModelDTO;
    name: string;
    projectId: number;
    testDataset: DatasetDTO;
    trainDataset: DatasetDTO;
}