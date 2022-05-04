/**
 * Generated from ai.giskard.web.dto.user.AdminUserDTO
 */
export interface AdminUserDTO {
    activated?: boolean | null;
    createdBy?: string | null;
    createdDate?: any /* TODO: Missing translation of java.time.Instant */ | null;
    display_name?: string | null;
    email: string;
    enabled?: boolean | null;
    firstName?: string | null;
    id?: number | null;
    imageUrl?: string | null;
    langKey?: string | null;
    lastModifiedBy?: string | null;
    lastModifiedDate?: any /* TODO: Missing translation of java.time.Instant */ | null;
    lastName?: string | null;
    roles?: string[] | null;
    user_id: string;
}

export namespace AdminUserDTO {
    /**
     * Generated from ai.giskard.web.dto.user.AdminUserDTO$AdminUserDTOWithPassword
     */
    export interface AdminUserDTOWithPassword extends AdminUserDTO {
        password: string;
    }
}