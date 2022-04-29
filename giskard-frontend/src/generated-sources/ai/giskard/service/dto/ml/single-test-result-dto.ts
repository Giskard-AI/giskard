/**
 * Generated from ai.giskard.service.dto.ml.SingleTestResultDTO
 */
export interface SingleTestResultDTO {
    elementCount: number;
    metric: number;
    missingCount: number;
    missingPercent: number;
    partialUnexpectedIndexList: number[];
    passed: boolean;
    unexpectedCount: number;
    unexpectedIndexList: number[];
    unexpectedPercent: number;
    unexpectedPercentNonmissing: number;
    unexpectedPercentTotal: number;
}