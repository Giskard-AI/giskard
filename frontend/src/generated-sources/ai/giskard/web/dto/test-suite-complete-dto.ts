import type {DatasetDTO} from './ml/dataset-dto';
import type {ModelDTO} from './ml/model-dto';
import type {RequiredInputDTO} from './required-input-dto';
import type {TestSuiteDTO} from './test-suite-dto';
import type {TestSuiteExecutionDTO} from './ml/test-suite-execution-dto';

/**
 * Generated from ai.giskard.web.dto.TestSuiteCompleteDTO
 */
export interface TestSuiteCompleteDTO {
    datasets: DatasetDTO[];
    executions: TestSuiteExecutionDTO[];
    inputs: {[key: string]: RequiredInputDTO};
    models: ModelDTO[];
    suite: TestSuiteDTO;
}
