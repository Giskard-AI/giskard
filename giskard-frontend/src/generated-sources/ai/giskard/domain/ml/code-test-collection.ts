import type {CodeTestTemplate} from './code-test-template';

/**
 * Generated from ai.giskard.domain.ml.CodeTestCollection
 */
export interface CodeTestCollection {
    id: string;
    items: CodeTestTemplate[];
    order: number;
    title: string;
}