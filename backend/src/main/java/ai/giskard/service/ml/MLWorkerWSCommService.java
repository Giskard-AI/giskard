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
        return performAction(workerID, action, param, 0);
    }

    @Transactional(propagation = Propagation.NEVER)
    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param, long milliseconds) {
        // Prepare to receive the final result
        UUID repId = UUID.randomUUID();
        mlWorkerWSService.prepareResultWaiter(repId.toString());

        // Prepare the parameters and publish message
        send(workerID, action, param, repId);

        String result = null;
        if (milliseconds > 0) {
            result = awaitReply(repId, milliseconds);
        } else {
            result = blockAwaitReply(repId);
        }

        if (result == null) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            log.warn("Received an empty reply for {} {}", action, repId);
            return null;
        }

        try {
            return switch (action) {
                case getInfo -> parseReplyDTO(result, MLWorkerWSGetInfoDTO.class);
                case runAdHocTest -> parseReplyDTO(result, MLWorkerWSRunAdHocTestDTO.class);
                case datasetProcessing -> parseReplyDTO(result, MLWorkerWSDatasetProcessingDTO.class);
                case runTestSuite -> parseReplyDTO(result, MLWorkerWSTestSuiteDTO.class);
                case runModel, stopWorker, generateQueryBasedSlicingFunction -> new MLWorkerWSEmptyDTO();
                case runModelForDataFrame -> parseReplyDTO(result, MLWorkerWSRunModelForDataFrameDTO.class);
                case explain -> parseReplyDTO(result, MLWorkerWSExplainDTO.class);
                case explainText -> parseReplyDTO(result, MLWorkerWSExplainTextDTO.class);
                case echo -> parseReplyDTO(result, MLWorkerWSEchoMsgDTO.class);
                case generateTestSuite -> parseReplyDTO(result, MLWorkerWSGenerateTestSuiteDTO.class);
                case getCatalog -> parseReplyDTO(result, MLWorkerWSCatalogDTO.class);
            };
        } catch (JsonProcessingException e) {
            return parseReplyErrorDTO(result);
        }
    }

    public UUID performActionAsync(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param) {
        // Prepare to receive the final result
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

    public <T> T parseReplyDTO(String result, Class<T> valueType) throws JsonProcessingException {
        ObjectMapper objectMapper = new ObjectMapper();
        return objectMapper.readValue(result, valueType);
    }

    public MLWorkerWSErrorDTO parseReplyErrorDTO(String result) {
        ObjectMapper objectMapper = new ObjectMapper();
        try {
            MLWorkerWSErrorDTO error = objectMapper.readValue(result, MLWorkerWSErrorDTO.class);
            log.warn("Parsed error: {}", error.getErrorStr());
            return error;
        } catch (JsonProcessingException e1) {
            log.warn("Not an valid error: {}", result);
        }
        return null;
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
