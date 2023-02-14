import type {TestInputDTO} from './test-input-dto';

/**
 * Generated from ai.giskard.web.dto.SuiteTestDTO
 */
export interface SuiteTestDTO {
    testInputs: {[key: string]: TestInputDTO};
    testUuid: string;
}