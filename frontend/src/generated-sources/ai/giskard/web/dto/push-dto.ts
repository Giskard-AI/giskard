import type {PushDetailsDTO} from './push-details-dto';
import {PushKind} from "@/generated-sources";

/**
 * Generated from ai.giskard.web.dto.PushDTO
 */
export interface PushDTO {
    details: PushDetailsDTO[];
    key: string;
    perturbationValue: string;
    push_title: string;
    value: string;
    kind: PushKind;
}