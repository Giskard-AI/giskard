/**
 * Generated from ai.giskard.web.dto.user.AdminUserDTO
 */
export interface AdminUserDTO {
    activated?: boolean | null;
    createdBy?: string | null;
    createdDate?: any /* TODO: Missing translation of java.time.Instant */ | null;
    displayName?: string | null;
    email: string;
    enabled?: boolean | null;
    id?: number | null;
    lastModifiedBy?: string | null;
    lastModifiedDate?: any /* TODO: Missing translation of java.time.Instant */ | null;
    roles?: string[] | null;
    user_id: string;
}

/**
 * Generated from ai.giskard.web.dto.user.AdminUserDTO$AdminUserDTOWithPassword
 */
export interface AdminUserDTOWithPassword extends AdminUserDTO {
    password: string;
}