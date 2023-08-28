package ai.giskard.service.ml;

import ai.giskard.config.WebSocketConfig;
import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerReplyMessage;
import ai.giskard.ml.MLWorkerReplyType;
import ai.giskard.ml.MLWorkerWSAction;
import ai.giskard.ml.dto.*;
import ai.giskard.service.AnalyticsCollectorService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.json.JSONObject;
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

import static ai.giskard.service.AnalyticsCollectorService.MLWorkerWebSocketTracking.*;

@Service
@RequiredArgsConstructor
public class MLWorkerWSCommService {
    private final Logger log = LoggerFactory.getLogger(MLWorkerWSCommService.class.getName());

    private final MLWorkerWSService mlWorkerWSService;
    private final AnalyticsCollectorService analyticsCollectorService;

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

    // This operation can be slow so that it should not be executed inside a DB transaction
    @Transactional(propagation = Propagation.NEVER)
    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param) {
        return performAction(workerID, action, param, 0);
    }

    // This operation can be slow so that it should not be executed inside a DB transaction
    @Transactional(propagation = Propagation.NEVER)
    public MLWorkerWSBaseDTO performAction(MLWorkerID workerID, MLWorkerWSAction action, MLWorkerWSBaseDTO param, long milliseconds) {
        JSONObject trackMsg = new JSONObject();
        trackMsg.put("name", action.toString());
        trackMsg.put("worker", workerID.toString());
        analyticsCollectorService.track(
            "MLWorker sync action type",
            trackMsg
        );
        long start = System.currentTimeMillis();

        // Prepare to receive the final result
        UUID repId = UUID.randomUUID();
        mlWorkerWSService.prepareResultWaiter(repId.toString());

        // Prepare the parameters and publish message
        send(workerID, action, param, repId);

        String result;
        if (milliseconds > 0) {
            result = awaitReply(repId, milliseconds);
        } else {
            result = blockAwaitReply(repId);
        }

        if (result == null) {
            mlWorkerWSService.removeResultWaiter(repId.toString());
            log.warn("Received an empty reply for {} {}", action, repId);

            // Track null message
            trackMsg.put(ACTION_TIME_FILED, System.currentTimeMillis() - start);
            trackMsg.put(TYPE_FILED, "ERROR");
            trackMsg.put(ERROR_FIELD, "Empty");
            trackMsg.put(ERROR_TYPE_FIELD, "Empty");
            analyticsCollectorService.track(
                "MLWorker sync action",
                trackMsg
            );
            return null;
        }

        MLWorkerWSBaseDTO reply = null;
        try {
            reply = switch (action) {
                case GET_INFO -> parseReplyDTO(result, MLWorkerWSGetInfoDTO.class);
                case RUN_AD_HOC_TEST -> parseReplyDTO(result, MLWorkerWSRunAdHocTestDTO.class);
                case DATASET_PROCESSING -> parseReplyDTO(result, MLWorkerWSDatasetProcessingDTO.class);
                case RUN_TEST_SUITE -> parseReplyDTO(result, MLWorkerWSTestSuiteDTO.class);
                case RUN_MODEL, STOP_WORKER, GENERATE_QUERY_BASED_SLICING_FUNCTION -> new MLWorkerWSEmptyDTO();
                case RUN_MODEL_FOR_DATA_FRAME -> parseReplyDTO(result, MLWorkerWSRunModelForDataFrameDTO.class);
                case EXPLAIN -> parseReplyDTO(result, MLWorkerWSExplainDTO.class);
                case EXPLAIN_TEXT -> parseReplyDTO(result, MLWorkerWSExplainTextDTO.class);
                case ECHO -> parseReplyDTO(result, MLWorkerWSEchoMsgDTO.class);
                case GENERATE_TEST_SUITE -> parseReplyDTO(result, MLWorkerWSGenerateTestSuiteDTO.class);
                case GET_CATALOG -> parseReplyDTO(result, MLWorkerWSCatalogDTO.class);
            };
        } catch (JsonProcessingException e) {
            reply = parseReplyErrorDTO(result);
        } finally {
            // Track reply or error message
            trackMsg.put(ACTION_TIME_FILED, System.currentTimeMillis() - start);
            if (reply instanceof MLWorkerWSErrorDTO error) {
                trackMsg.put(TYPE_FILED, "ERROR");
                trackMsg.put(ERROR_FIELD, error.getErrorStr());
                trackMsg.put(ERROR_TYPE_FIELD, error.getErrorType());
            } else {
                trackMsg.put(TYPE_FILED, "SUCCESS");
                trackMsg.put(ERROR_FIELD, "");
                trackMsg.put(ERROR_TYPE_FIELD, "");
            }
            analyticsCollectorService.track(
                "MLWorker sync action",
                trackMsg
            );
        }
        return reply;
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
