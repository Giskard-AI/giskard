import type {ColumnMeaning} from './../../domain/column-meaning';

/**
 * Generated from ai.giskard.web.dto.FeatureMetadataDTO
 */
export interface FeatureMetadataDTO {
    name: string;
    type: ColumnMeaning;
    values: string[];
}