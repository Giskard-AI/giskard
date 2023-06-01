import type {DatasetDTO} from './dataset-dto';
import type {ModelDTO} from './model-dto';
import type {ProjectDTO} from './project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.FileDTO
 */
export interface _FileDTO {
    createdDate: any /* TODO: Missing translation of java.time.Instant */;
    fileName: string;
    id: number;
    name: string;
    project: ProjectDTO;
    size: number;
}

export type FileDTO = DatasetDTO | ModelDTO;