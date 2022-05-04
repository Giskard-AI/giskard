import type {CodeLanguage} from './../../../domain/ml/code-language';

/**
 * Generated from ai.giskard.web.dto.ml.CodeBasedTestPresetDTO
 */
export interface CodeBasedTestPresetDTO {
    code: string;
    id: number;
    language: CodeLanguage;
    name: string;
}