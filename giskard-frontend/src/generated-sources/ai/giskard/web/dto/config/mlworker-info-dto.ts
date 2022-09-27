/**
 * Generated from ai.giskard.web.dto.config.MLWorkerInfoDTO
 */
export interface MLWorkerInfoDTO {
    installedPackages: {[key: string]: string};
    internalGrpcPort: number;
    interpreter: string;
    interpreterVersion: string;
    isRemote: boolean;
    platform: MLWorkerInfoDTO.PlatformInfoDTO;
}

export namespace MLWorkerInfoDTO {
    /**
     * Generated from ai.giskard.web.dto.config.MLWorkerInfoDTO$PlatformInfoDTO
     */
    export interface PlatformInfoDTO {
        machine: string;
        node: string;
        processor: string;
        release: string;
        system: string;
        version: string;
    }
}