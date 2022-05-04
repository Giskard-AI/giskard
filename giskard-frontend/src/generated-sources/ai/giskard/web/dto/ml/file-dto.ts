import type {DatasetDTO} from './dataset-dto';
import type {ModelDTO} from './model-dto';
import type {ProjectDTO} from './project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.FileDTO
 */
export interface _FileDTO {
    creation_date: any /* TODO: Missing translation of java.time.LocalDateTime */;
    file_name: string;
    id: number;
    location: string;
    name: string;
    project: ProjectDTO;
}

export type FileDTO = DatasetDTO | ModelDTO;