import type {NestedPostDTO} from './nested-post-dto';

/**
 * Generated from ai.giskard.web.dto.ml.TestSuitePostDTO
 */
export interface TestSuitePostDTO {
    id: number;
    model: NestedPostDTO;
    name: string;
    project: NestedPostDTO;
    testDataset: NestedPostDTO;
    trainDataset: NestedPostDTO;
}