/**
 * Generated from ai.giskard.web.dto.CreateFeedbackDTO
 */
export interface CreateFeedbackDTO {
    datasetId: any /* TODO: Missing translation of java.util.UUID */;
    featureName?: string | null;
    featureValue?: string | null;
    feedbackChoice?: string | null;
    feedbackMessage?: string | null;
    feedbackType: string;
    modelId: any /* TODO: Missing translation of java.util.UUID */;
    originalData: string;
    projectId: number;
    targetFeature?: string | null;
    userData: string;
}