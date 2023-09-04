import type {AdminUserDTO} from './../user/admin-user-dto';
import type {GeneralSettings} from './../../../domain/general-settings';
import type {LicenseDTO} from './license-dto';
import type {RoleDTO} from './../user/role-dto';

/**
 * Generated from ai.giskard.web.dto.config.AppConfigDTO
 */
export interface AppConfigDTO {
    app: AppInfoDTO;
    license: LicenseDTO;
    user: AdminUserDTO;
}

export interface AppInfoDTO {
    buildBranch: string;
    buildCommitId: string;
    buildCommitTime: any /* TODO: Missing translation of java.time.Instant */
    ;
    externalMlWorkerEntrypointHost: string;
    externalMlWorkerEntrypointPort: number;
    generalSettings: GeneralSettings;
    hfSpaceId: string;
    isRunningOnHfSpaces: boolean;
    planCode: string;
    planName: string;
    roles: RoleDTO[];
    seatsAvailable: number;
    version: string;
}