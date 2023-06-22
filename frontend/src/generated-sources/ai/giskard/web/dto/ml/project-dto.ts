import type { MLWorkerType } from './../../../domain/mlworker-type';
import type { UserDTO } from './../user/user-dto';

/**
 * Generated from ai.giskard.web.dto.ml.ProjectDTO
 */
export interface ProjectDTO {
    createdDate: any /* TODO: Missing translation of java.time.Instant */
    ;
    description: string;
    guests: UserDTO[];
    id: number;
    key: string;
    mlWorkerType: MLWorkerType;
    name: string;
    owner: UserDTO;
}
