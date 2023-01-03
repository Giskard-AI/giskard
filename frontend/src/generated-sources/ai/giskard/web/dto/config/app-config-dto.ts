import type {AdminUserDTO} from './../user/admin-user-dto';
import type {FeatureFlagService} from './../../../service/ee/feature-flag-service';
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
        buildBranch: string;
        buildCommitId: string;
        buildCommitTime: any /* TODO: Missing translation of java.time.Instant */;
        externalMlWorkerEntrypointPort: number;
        features: {[key in FeatureFlagService.FeatureFlag]: boolean};
        generalSettings: GeneralSettings;
        planCode: string;
        planName: string;
        roles: RoleDTO[];
        seatsAvailable: number;
        version: string;
    }
}