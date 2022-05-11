import type {DatasetDTO} from './../dataset-dto';
import type {ModelDTO} from './../model-dto';
import type {ProjectDTO} from './../project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.write.TestSuitePostDTO
 */
export interface TestSuitePostDTO {
    id: number;
    model: ModelDTO;
    name: string;
    project: ProjectDTO;
    testDataset: DatasetDTO;
    trainDataset: DatasetDTO;
}