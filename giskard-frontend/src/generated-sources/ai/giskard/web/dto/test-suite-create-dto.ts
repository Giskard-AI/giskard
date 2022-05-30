/**
 * Generated from ai.giskard.web.dto.TestSuiteCreateDTO
 */
export interface TestSuiteCreateDTO {
    modelId: number;
    name: string;
    projectId: number;
    shouldGenerateTests: boolean;
    testDatasetId?: number | null;
    trainDatasetId?: number | null;
}