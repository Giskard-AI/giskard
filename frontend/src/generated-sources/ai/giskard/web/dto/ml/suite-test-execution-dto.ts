import type { SuiteTestDTO } from './../suite-test-dto';
import type { TestResultMessageDTO } from './test-result-message-dto';
import type { TestResult } from './../../../domain/ml/test-result';

/**
 * Generated from ai.giskard.web.dto.ml.SuiteTestExecutionDTO
 */
export interface SuiteTestExecutionDTO {
  actualSlicesSize: number[];
  inputs: { [key: string]: string };
  messages: TestResultMessageDTO[];
  metric: number;
  missingCount: number;
  missingPercent: number;
  partialUnexpectedIndexList: number[];
  referenceSlicesSize: number[];
  status: TestResult;
  test: SuiteTestDTO;
  unexpectedCount: number;
  unexpectedIndexList: number[];
  unexpectedPercent: number;
  unexpectedPercentNonmissing: number;
  unexpectedPercentTotal: number;
}
