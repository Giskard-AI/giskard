/**
 * Generated from ai.giskard.web.dto.CreateFeedbackDTO
 */
export interface CreateFeedbackDTO {
    datasetId: string;
    featureName?: string | null;
    featureValue?: string | null;
    feedbackChoice?: string | null;
    feedbackMessage?: string | null;
    feedbackType: string;
    modelId: string;
    originalData: string;
    projectId: number;
    targetFeature?: string | null;
    userData: string;
}