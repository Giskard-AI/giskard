package ai.giskard.web.rest.controllers;

import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.MLWorkerWSBaseDTO;
import ai.giskard.ml.dto.MLWorkerWSGetInfoDTO;
import ai.giskard.ml.dto.MLWorkerWSGetInfoParamDTO;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.service.ml.MLWorkerWSCommService;
import ai.giskard.service.ml.MLWorkerWSService;
import ai.giskard.web.dto.config.MLWorkerInfoDTO;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/ml-workers")
public class MLWorkerController {
    private final Logger log = LoggerFactory.getLogger(getClass());
    private final MLWorkerService mlWorkerService;
    private final MLWorkerWSService mlWorkerWSService;
    private final MLWorkerWSCommService mlWorkerWSCommService;
    private final ObjectMapper objectMapper = new ObjectMapper();

    @GetMapping()
    public List<MLWorkerInfoDTO> getMLWorkerInfo()
            throws JsonProcessingException {
        List<MLWorkerWSGetInfoDTO> results = new ArrayList<>();

        MLWorkerWSGetInfoParamDTO param = MLWorkerWSGetInfoParamDTO.builder()
            .listPackages(true).build();
        if (mlWorkerWSService.isWorkerConnected(MLWorkerID.INTERNAL)) {

            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                MLWorkerID.INTERNAL,
                MLWorkerWSAction.getInfo,
                param
            );
            if (result instanceof MLWorkerWSGetInfoDTO info) {
                results.add(info);
            }
        }
        if (mlWorkerWSService.isWorkerConnected(MLWorkerID.EXTERNAL)) {
            MLWorkerWSBaseDTO result = mlWorkerWSCommService.performAction(
                MLWorkerID.EXTERNAL,
                MLWorkerWSAction.getInfo,
                param
            );
            if (result instanceof MLWorkerWSGetInfoDTO info) {
                results.add(info);
            }
        }

        List<MLWorkerInfoDTO> res = new ArrayList<>();
        for (MLWorkerWSBaseDTO info : results) {
            if (info != null) {
                res.add(new ObjectMapper().readValue(objectMapper.writeValueAsString(info), MLWorkerInfoDTO.class));
            }
        }

        return res;
    }

    @PostMapping("/stop")
    public void stopWorker(boolean internal) {
        MLWorkerID workerID = internal ? MLWorkerID.INTERNAL : MLWorkerID.EXTERNAL;
        if (mlWorkerWSService.isWorkerConnected(workerID)) {
            mlWorkerWSCommService.performAction(workerID, MLWorkerWSAction.stopWorker, null);
        }
    }

    @GetMapping("/external/connected")
    public boolean isExternalWorkerConnected() {
        return mlWorkerService.isExternalWorkerConnected();
    }
}
