/**
 * Generated from ai.giskard.web.dto.TestSuiteCreateDTO
 */
export interface TestSuiteCreateDTO {
    actualDatasetId?: string | null;
    modelId: string;
    name: string;
    projectId: number;
    referenceDatasetId?: string | null;
    shouldGenerateTests: boolean;
}