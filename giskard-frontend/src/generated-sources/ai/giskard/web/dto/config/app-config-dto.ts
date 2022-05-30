import type {AdminUserDTO} from './../user/admin-user-dto';
import type {RoleDTO} from './../user/role-dto';

/**
 * Generated from ai.giskard.web.dto.config.AppConfigDTO
 */
export interface AppConfigDTO {
    app: AppConfigDTO.AppInfoDTO;
    user: AdminUserDTO;
}

export namespace AppConfigDTO {
    /**
     * Generated from ai.giskard.web.dto.config.AppConfigDTO$AppInfoDTO
     */
    export interface AppInfoDTO {
        plan_code: string;
        plan_name: string;
        roles: RoleDTO[];
        seats_available: number;
    }
}