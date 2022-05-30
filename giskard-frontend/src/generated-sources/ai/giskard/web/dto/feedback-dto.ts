import type {DatasetDTO} from './ml/dataset-dto';
import type {FeedbackReplyDTO} from './feedback-reply-dto';
import type {ModelDTO} from './ml/model-dto';
import type {ProjectDTO} from './ml/project-dto';
import type {UserMinimalDTO} from './user/user-minimal-dto';

/**
 * Generated from ai.giskard.web.dto.FeedbackDTO
 */
export interface FeedbackDTO {
    createdOn: any /* TODO: Missing translation of java.time.Instant */;
    dataset: DatasetDTO;
    featureName: string;
    featureValue: string;
    feedbackChoice: string;
    feedbackMessage: string;
    feedbackReplies: FeedbackReplyDTO[];
    feedbackType: string;
    id: number;
    model: ModelDTO;
    originalData: string;
    project: ProjectDTO;
    targetFeature: string;
    user: UserMinimalDTO;
    userData: string;
}