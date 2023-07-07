import type {PushDetailsDTO} from './push-details-dto';

/**
 * Generated from ai.giskard.web.dto.PushDTO
 */
export interface PushDTO {
    details: PushDetailsDTO[];
    key: string;
    kind: any /* TODO: Missing translation of ai.giskard.worker.PushKind */;
    perturbationValue: string;
    pushTitle: string;
    value: string;
}