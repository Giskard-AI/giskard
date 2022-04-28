import type {AdminUserDTO} from './../admin-user-dto';

/**
 * Generated from ai.giskard.service.dto.config.AppConfigDTO
 */
export interface AppConfigDTO {
    app: AppConfigDTO.AppInfoDTO;
    user: AdminUserDTO.AdminUserDTOMigration;
}

export namespace AppConfigDTO {
    /**
     * Generated from ai.giskard.service.dto.config.AppConfigDTO$AppInfoDTO
     */
    export interface AppInfoDTO {
        plan_code: string;
        plan_name: string;
        seats_available: number;
    }
}