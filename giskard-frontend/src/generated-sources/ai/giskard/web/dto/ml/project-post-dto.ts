import type {InspectionSettings} from './../../../domain/inspection-settings';

/**
 * Generated from ai.giskard.web.dto.ml.ProjectPostDTO
 */
export interface ProjectPostDTO {
    description: string;
    id?: number | null;
    inspectionSettings: InspectionSettings;
    key?: string | null;
    name: string;
}