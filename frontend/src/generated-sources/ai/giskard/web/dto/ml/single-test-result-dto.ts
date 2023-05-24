import type {TestResultMessageDTO} from './test-result-message-dto';

/**
 * Generated from ai.giskard.web.dto.ml.SingleTestResultDTO
 */
export interface SingleTestResultDTO {
    actualSlicesSize: number[];
    messages: TestResultMessageDTO[];
    metric: number;
    missingCount: number;
    missingPercent: number;
    outputDfUuid: string;
    partialUnexpectedIndexList: number[];
    passed: boolean;
    referenceSlicesSize: number[];
    unexpectedCount: number;
    unexpectedIndexList: number[];
    unexpectedPercent: number;
    unexpectedPercentNonmissing: number;
    unexpectedPercentTotal: number;
}