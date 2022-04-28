import type {ProjectDTO} from './project-dto';

/**
 * Generated from ai.giskard.service.dto.ml.ModelDTO
 */
export interface ModelDTO {
    creation_date: any /* TODO: Missing translation of java.time.LocalDateTime */;
    filename: string;
    id: number;
    location: string;
    name: string;
    project: ProjectDTO;
    python_version: string;
}