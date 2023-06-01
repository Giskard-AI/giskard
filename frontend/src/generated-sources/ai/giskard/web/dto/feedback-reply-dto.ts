import type {UserMinimalDTO} from './user/user-minimal-dto';

/**
 * Generated from ai.giskard.web.dto.FeedbackReplyDTO
 */
export interface FeedbackReplyDTO {
    content: string;
    createdOn: any /* TODO: Missing translation of java.time.Instant */;
    feedbackId: number;
    id: number;
    replyToReply: number;
    user: UserMinimalDTO;
}