import type {AdminUserDTO} from './../user/admin-user-dto';
import type {GeneralSettings} from './../../../domain/general-settings';
import type {LicenseDTO} from './license-dto';
import type {RoleDTO} from './../user/role-dto';

/**
 * Generated from ai.giskard.web.dto.config.AppConfigDTO
 */
export interface AppConfigDTO {
    app: AppConfigDTO.AppInfoDTO;
    license: LicenseDTO;
    user: AdminUserDTO;
}

export namespace AppConfigDTO {
    /**
     * Generated from ai.giskard.web.dto.config.AppConfigDTO$AppInfoDTO
     */
    export interface AppInfoDTO {
        buildBranch: string;
        buildCommitId: string;
        buildCommitTime: any /* TODO: Missing translation of java.time.Instant */;
        externalMlWorkerEntrypointHost: string;
        externalMlWorkerEntrypointPort: number;
        generalSettings: GeneralSettings;
        planCode: string;
        planName: string;
        roles: RoleDTO[];
        seatsAvailable: number;
        version: string;
    }
}