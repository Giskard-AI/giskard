import type {SlicingFunctionDTO} from './slicing-function-dto';
import type {TestFunctionDTO} from './test-function-dto';
import type {TransformationFunctionDTO} from './transformation-function-dto';

/**
 * Generated from ai.giskard.web.dto.CatalogDTO
 */
export interface CatalogDTO {
    slices: SlicingFunctionDTO[];
    tests: TestFunctionDTO[];
    transformations: TransformationFunctionDTO[];
}