import type {CallToActionKind} from './../../domain/ml/call-to-action-kind';
import type {PushKind} from './../../domain/ml/push-kind';

/**
 * Generated from ai.giskard.web.dto.ApplyPushDTO
 */
export interface ApplyPushDTO {
    ctaKind: CallToActionKind;
    datasetId: string;
    features: {[key: string]: string};
    modelId: string;
    pushKind: PushKind;
    rowIdx: number;
}