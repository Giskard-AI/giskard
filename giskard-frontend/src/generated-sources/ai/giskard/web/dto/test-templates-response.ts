import type {CodeTestCollection} from './../../domain/ml/code-test-collection';

/**
 * Generated from ai.giskard.web.dto.TestTemplatesResponse
 */
export interface TestTemplatesResponse {
    collections: CodeTestCollection[];
    testAvailability: {[key: string]: boolean};
}