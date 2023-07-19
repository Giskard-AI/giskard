package ai.giskard.service.ml;

import ai.giskard.config.WebSocketConfig;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.UUID;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class MLWorkerWSCommService {
    private final Logger log = LoggerFactory.getLogger(MLWorkerWSCommService.class.getName());

    private final MLWorkerWSService mlWorkerWSService;

    private final SimpMessagingTemplate simpMessagingTemplate;

    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param)
            throws NullPointerException, JsonProcessingException {
        // Wait for result during 5 seconds/5000 milliseconds
        return this.performAction(workerID, action, param, 5000);
    }

    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param, long milliseconds)
            throws NullPointerException, JsonProcessingException {
        // Prepare to receive a one-shot result
        UUID repId = UUID.randomUUID();
        BlockingQueue<String> queue = mlWorkerWSService.getResultWaiter(repId.toString(), true);

        // Prepare the parameters and publish message
        HashMap<String, Object> data = new HashMap<>();
        data.put("action", action.toString());
        data.put("id", repId.toString());
        data.put("param", param);
        simpMessagingTemplate.convertAndSend(
            String.join("/", WebSocketConfig.ML_WORKER_TOPIC_PREFIX, workerID.toString(), WebSocketConfig.ML_WORKER_ACTION_TOPIC),
            data
        );

        String result = null;
        try {
            // Waiting for the result
            result = queue.poll(milliseconds, TimeUnit.MILLISECONDS);
        } catch (InterruptedException e) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            Thread.currentThread().interrupt();
        }

        if (result == null) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            log.warn("Received an empty reply for {} {}", action, repId);
            throw new NullPointerException("Received an empty reply for " + action);
        }

        ObjectMapper objectMapper = new ObjectMapper();
        try {
            return switch (action) {
                case getInfo -> objectMapper.readValue(result, MLWorkerWSGetInfoDTO.class);
                case runAdHocTest -> objectMapper.readValue(result, MLWorkerWSRunAdHocTestDTO.class);
                case datasetProcessing -> objectMapper.readValue(result, MLWorkerWSDatasetProcessingDTO.class);
                case runTestSuite -> objectMapper.readValue(result, MLWorkerWSTestSuiteDTO.class);
                case runModel, stopWorker, generateQueryBasedSlicingFunction -> null;
                case runModelForDataFrame -> objectMapper.readValue(result, MLWorkerWSRunModelForDataFrameDTO.class);
                case explain -> objectMapper.readValue(result, MLWorkerWSExplainDTO.class);
                case explainText -> objectMapper.readValue(result, MLWorkerWSExplainTextDTO.class);
                case echo -> objectMapper.readValue(result, MLWorkerWSEchoMsgDTO.class);
                case generateTestSuite -> objectMapper.readValue(result, MLWorkerWSGenerateTestSuiteDTO.class);
                case getCatalog -> objectMapper.readValue(result, MLWorkerWSCatalogDTO.class);
            };
        } catch (JsonProcessingException e) {
            // Parse error information
            log.warn("Deserialization failed: {}", e.getMessage());
            MLWorkerWSErrorDTO error = objectMapper.readValue(result, MLWorkerWSErrorDTO.class);
            log.warn("Parsed error: {}", error.getErrorStr());
            throw new NullPointerException(error.getErrorStr());
        }
    }
}
