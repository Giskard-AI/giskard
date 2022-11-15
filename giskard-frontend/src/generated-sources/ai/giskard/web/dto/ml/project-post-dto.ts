import type {InspectionSettings} from './../../../domain/inspection-settings';

/**
 * Generated from ai.giskard.web.dto.ml.ProjectPostDTO
 */
export interface ProjectPostDTO {
    description: string;
    id?: number | null;
    inspectionSettings?: InspectionSettings | null;
    key?: string | null;
    name: string;
}