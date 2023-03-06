import type {FeatureFlag} from './../../../service/ee/feature-flag';

/**
 * Generated from ai.giskard.web.dto.config.LicenseDTO
 */
export interface LicenseDTO {
    active: boolean;
    features: {[key in FeatureFlag]: boolean};
    planCode: string;
    planName: string;
    projectLimit: number;
    userLimit: number;
}