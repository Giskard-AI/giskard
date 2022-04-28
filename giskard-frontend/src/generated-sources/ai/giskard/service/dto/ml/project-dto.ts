import type {UserDTO} from './../user-dto';

/**
 * Generated from ai.giskard.service.dto.ml.ProjectDTO
 */
export interface ProjectDTO {
    created_on: any /* TODO: Missing translation of java.time.LocalDateTime */;
    guest_list: UserDTO[];
    id: number;
    key: string;
    name: string;
    owner_details: UserDTO;
}