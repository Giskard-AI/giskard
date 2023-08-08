package ai.giskard.service.ml;

import ai.giskard.config.WebSocketConfig;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerReplyMessage;
import ai.giskard.ml.MLWorkerReplyType;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

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

    public void notifyMaxReplyPayloadLength(MLWorkerID workerID, int maxPayloadLength) {
        // Prepare the parameters and publish message
        HashMap<String, Object> data = new HashMap<>();
        data.put("config", "MAX_STOMP_ML_WORKER_REPLY_SIZE");
        data.put("value", maxPayloadLength);
        simpMessagingTemplate.convertAndSend(
            String.join("/", WebSocketConfig.ML_WORKER_TOPIC_PREFIX, workerID.toString(), WebSocketConfig.ML_WORKER_CONFIG_TOPIC),
            data
        );
    }

    @Transactional(propagation = Propagation.NEVER)
    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param) {
        // Prepare to receive a one-shot result
        UUID repId = UUID.randomUUID();
        mlWorkerWSService.prepareResultWaiter(repId.toString());

        // Prepare the parameters and publish message
        send(workerID, action, param, repId);

        String result = blockAwaitReply(repId);
        if (result == null) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            log.warn("Received an empty reply for {} {}", action, repId);
            return null;
        }

        return parseReplyDTO(action, result);
    }

    @Transactional(propagation = Propagation.NEVER)
    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param, long milliseconds) {
        // Prepare to receive a one-shot result
        UUID repId = UUID.randomUUID();
        mlWorkerWSService.prepareResultWaiter(repId.toString());

        // Prepare the parameters and publish message
        send(workerID, action, param, repId);

        String result = awaitReply(repId, milliseconds);

        if (result == null) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            log.warn("Received an empty reply for {} {}", action, repId);
            return null;
        }

        return parseReplyDTO(action, result);
    }

    public UUID triggerAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param) {
        // Prepare to receive a one-shot result
        UUID repId = UUID.randomUUID();
        mlWorkerWSService.prepareResultWaiter(repId.toString());

        // Prepare the parameters and publish message
        send(workerID, action, param, repId);

        return repId;
    }

    private void send(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param, UUID repId) {
        HashMap<String, Object> data = new HashMap<>();
        data.put("action", action.toString());
        data.put("id", repId.toString());
        data.put("param", param);
        simpMessagingTemplate.convertAndSend(
            String.join("/", WebSocketConfig.ML_WORKER_TOPIC_PREFIX, workerID.toString(), WebSocketConfig.ML_WORKER_ACTION_TOPIC),
            data
        );
    }

    public MLWorkerWSBaseDTO parseReplyDTO(MLWorkerWSAction action, String result) {
        ObjectMapper objectMapper = new ObjectMapper();
        try {
            return switch (action) {
                case getInfo -> objectMapper.readValue(result, MLWorkerWSGetInfoDTO.class);
                case runAdHocTest -> objectMapper.readValue(result, MLWorkerWSRunAdHocTestDTO.class);
                case datasetProcessing -> objectMapper.readValue(result, MLWorkerWSDatasetProcessingDTO.class);
                case runTestSuite -> objectMapper.readValue(result, MLWorkerWSTestSuiteDTO.class);
                case runModel, stopWorker, generateQueryBasedSlicingFunction -> new MLWorkerWSEmptyDTO();
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
            try {
                MLWorkerWSErrorDTO error = objectMapper.readValue(result, MLWorkerWSErrorDTO.class);
                log.warn("Parsed error: {}", error.getErrorStr());
                return error;
            } catch (JsonProcessingException e1) {
                log.warn("Neither a reply nor an error: {}", result);
                return null;
            }
        }
    }

    public String awaitReply(UUID repId, long milliseconds) {
        String result = null;
        BlockingQueue<MLWorkerReplyMessage> queue = mlWorkerWSService.getResultWaiter(repId.toString());
        try {
            // Waiting for the result
            long begin = System.currentTimeMillis();
            MLWorkerReplyMessage message = null;
            do {
                long timeout = Math.max(begin + milliseconds - System.currentTimeMillis(), 0);
                if (timeout == 0) break;

                message = queue.poll(timeout, TimeUnit.MILLISECONDS);
            } while (message == null || message.getType() != MLWorkerReplyType.FINISH);
            if (message != null && message.getType() == MLWorkerReplyType.FINISH) {
                result = message.getMessage();
                // Remove waiter after receiving the final reply
                mlWorkerWSService.removeResultWaiter(repId.toString());
            }
        } catch (InterruptedException e) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            Thread.currentThread().interrupt();
        }
        return result;
    }

    public String blockAwaitReply(UUID repId) {
        String result = null;
        BlockingQueue<MLWorkerReplyMessage> queue = mlWorkerWSService.getResultWaiter(repId.toString());
        try {
            // Waiting for the result
            MLWorkerReplyMessage message;
            do {
                message = queue.take();
            } while (message.getType() != MLWorkerReplyType.FINISH);
            result = message.getMessage();
            // Remove waiter after receiving the final reply
            mlWorkerWSService.removeResultWaiter(repId.toString());
        } catch (InterruptedException e) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            Thread.currentThread().interrupt();
        }
        return result;
    }
}
