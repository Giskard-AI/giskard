/**
 * Generated from ai.giskard.web.dto.config.MLWorkerInfoDTO
 */
export interface MLWorkerInfoDTO {
    giskardClientVersion: string;
    installedPackages: {[key: string]: string};
    interpreter: string;
    interpreterVersion: string;
    isRemote: boolean;
    mlWorkerId: string;
    pid: number;
    platform: MLWorkerInfoDTO.PlatformInfoDTO;
    processStartTime: number;
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