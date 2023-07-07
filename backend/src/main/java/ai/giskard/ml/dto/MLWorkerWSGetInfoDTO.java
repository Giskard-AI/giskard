package ai.giskard.ml.dto;

import lombok.Getter;

import java.util.HashMap;

@Getter
public class MLWorkerWSGetInfoDTO implements MLWorkerWSBaseDTO {

    private MLWorkerWSPlatformDTO platform;

    private String interpreter;

    private String interpreterVersion;

    private HashMap<String, String> installedPackages;

    private String internalGrpcAddress;

    private Boolean isRemote;

    private int pid;

    private long processStartTime;

    private String giskardClientVersion;
}
