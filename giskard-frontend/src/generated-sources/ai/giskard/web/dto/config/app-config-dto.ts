import type {AdminUserDTO} from './../user/admin-user-dto';
import type {GeneralSettings} from './../../../domain/general-settings';
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
        generalSettings: GeneralSettings;
        planCode: string;
        planName: string;
        roles: RoleDTO[];
        seatsAvailable: number;
        version: string;
    }
}