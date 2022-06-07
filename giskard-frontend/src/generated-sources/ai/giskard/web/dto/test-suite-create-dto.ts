/**
 * Generated from ai.giskard.web.dto.TestSuiteCreateDTO
 */
export interface TestSuiteCreateDTO {
    actualDatasetId?: number | null;
    modelId: number;
    name: string;
    projectId: number;
    referenceDatasetId?: number | null;
    shouldGenerateTests: boolean;
}