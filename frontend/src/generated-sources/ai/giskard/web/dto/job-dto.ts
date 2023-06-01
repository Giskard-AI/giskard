import type {JobState} from './../../jobs/job-state';
import type {JobType} from './../../jobs/job-type';
import type {MLWorkerType} from './../../domain/mlworker-type';

/**
 * Generated from ai.giskard.web.dto.JobDTO
 */
export interface JobDTO {
    jobType: JobType;
    mlWorkerType: MLWorkerType;
    progress: number;
    projectId: number;
    scheduledDate: any /* TODO: Missing translation of java.util.Date */;
    state?: JobState | null;
}