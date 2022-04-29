import type {Role} from './../../domain/role';

/**
 * Generated from ai.giskard.service.dto.AdminUserDTO
 */
export interface AdminUserDTO {
    createdBy: string;
    createdDate: any /* TODO: Missing translation of java.time.Instant */;
    display_name: string;
    email: string;
    firstName: string;
    id: number;
    imageUrl: string;
    is_active: boolean;
    langKey: string;
    lastModifiedBy: string;
    lastModifiedDate: any /* TODO: Missing translation of java.time.Instant */;
    lastName: string;
    roles: string[];
    user_id: string;
}

export namespace AdminUserDTO {
    /**
     * Generated from ai.giskard.service.dto.AdminUserDTO$AdminUserDTOMigration
     */
    export interface AdminUserDTOMigration extends AdminUserDTO {
        role: Role;
    }
}