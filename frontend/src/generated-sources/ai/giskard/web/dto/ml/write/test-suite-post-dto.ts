import type {DatasetDTO} from './../dataset-dto';
import type {ModelDTO} from './../model-dto';
import type {ProjectDTO} from './../project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.write.TestSuitePostDTO
 */
export interface TestSuitePostDTO {
    actualDataset: DatasetDTO;
    id: number;
    model: ModelDTO;
    name: string;
    project: ProjectDTO;
    referenceDataset: DatasetDTO;
}