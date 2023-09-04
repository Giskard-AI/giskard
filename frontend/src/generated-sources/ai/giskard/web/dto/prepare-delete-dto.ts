/**
 * Generated from ai.giskard.web.dto.PrepareDeleteDTO
 */
export interface PrepareDeleteDTO {
    feedbacks: LightFeedback[];
    suites: LightTestSuite[];
    totalUsage: number;
}

/**
 * Generated from ai.giskard.web.dto.PrepareDeleteDTO$LightTestSuite
 */
export interface LightTestSuite {
    id: number;
    name: string;
    projectId: number;
}

/**
 * Generated from ai.giskard.web.dto.PrepareDeleteDTO$LightFeedback
 */
export interface LightFeedback {
    id: number;
    message: string;
    projectId: number;
}