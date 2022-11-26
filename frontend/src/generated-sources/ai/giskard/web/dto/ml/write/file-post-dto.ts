import type {ModelPostDTO} from './model-post-dto';
import type {ProjectDTO} from './../project-dto';

/**
 * Generated from ai.giskard.web.dto.ml.write.FilePostDTO
 */
export interface _FilePostDTO {
    creation_date: any /* TODO: Missing translation of java.time.LocalDateTime */;
    file_name: string;
    id: number;
    location: string;
    name: string;
    project: ProjectDTO;
}

export type FilePostDTO = ModelPostDTO;