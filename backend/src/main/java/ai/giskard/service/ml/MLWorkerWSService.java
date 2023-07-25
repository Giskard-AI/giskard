package ai.giskard.service.ml;

import ai.giskard.ml.MLWorkerID;
import ai.giskard.ml.MLWorkerReplyAggregator;
import ai.giskard.ml.MLWorkerReplyMessage;
import ai.giskard.ml.MLWorkerReplyType;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class MLWorkerWSService {
    private final Logger log = LoggerFactory.getLogger(MLWorkerWSService.class);

    private final ConcurrentHashMap<String, String> workers = new ConcurrentHashMap<>();
    private String potentialInternalWorkerId;

    private final ConcurrentHashMap<String, MLWorkerReplyAggregator> messagePool = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, BlockingQueue<MLWorkerReplyMessage>> finalMessagePool = new ConcurrentHashMap<>();

    public boolean prepareInternalWorker(@NonNull String uuid) {
        if (uuid.equals(potentialInternalWorkerId)) return false;

        potentialInternalWorkerId = uuid;
        return true;
    }

    public boolean associateWorker(@NonNull String id, @NonNull String uuid) {
        if (uuid.equals(workers.get(id))) {
            // Duplicated, could be an attacker
            return false;
        }
        // Check for internal worker
        if (id.equals(MLWorkerID.INTERNAL.toString()) && !uuid.equals(this.potentialInternalWorkerId)) {
            // UUID not matched, could be an attacker
            return false;
        }

        workers.put(id, uuid);
        return true;
    }

    public boolean removeWorker(@NonNull String uuid) {
        if (uuid.equals(potentialInternalWorkerId)) {
            // Clear the memorized internal worker id
            potentialInternalWorkerId = null;
        }

        if (!workers.containsValue(uuid)) {
            // Not an ML Worker connection
            return false;
        }

        // Try to firstly remove the external worker
        if (!workers.remove(MLWorkerID.EXTERNAL.toString(), uuid)) {
            // Otherwise could be an internal worker
            return workers.remove(MLWorkerID.INTERNAL.toString(), uuid);
        }
        return true;
    }

    public void appendReply(String repId, int fragmentIndex, int fragmentCount, String result) {
        String fullReply = aggregateReply(repId, fragmentIndex, fragmentCount, result);
        if (fullReply != null) {
            this.attachResult(repId, fullReply);
        }
    }

    public void appendReply(String repId, int fragmentIndex, int fragmentCount, int index, int total, String result) {
        String fullReply = aggregateReply(repId + "-" + index, fragmentIndex, fragmentCount, result);
        if (fullReply != null) {
            this.attachResult(repId, fullReply, false, index, total);
        }
    }

    private String aggregateReply(String repId, int fragmentIndex, int fragmentCount, String result) {
        synchronized (messagePool) {
            MLWorkerReplyAggregator aggregator;
            if (!messagePool.containsKey(repId)) {
                aggregator = new MLWorkerReplyAggregator(fragmentCount);
                messagePool.put(repId, aggregator);
            } else {
                aggregator = messagePool.get(repId);
            }
            String previous = aggregator.addReply(fragmentIndex, result);
            if (StringUtils.hasText(previous))
                log.debug("Replaced {} with {} in reply {}", previous, result, repId);

            if (aggregator.isFinished()) {
                return aggregator.aggregate();
            }
        }
        return null;
    }

    public void attachResult(String repId, String result) {
        attachResult(repId, result, true, 0, 1);
    }

    public void attachResult(String repId, String result, boolean isOneShot, int index, int total) {
        synchronized (finalMessagePool) {
            if (finalMessagePool.containsKey(repId)) {
                BlockingQueue<MLWorkerReplyMessage> bq = finalMessagePool.get(repId);
                if (isOneShot) {
                    if (!bq.offer(MLWorkerReplyMessage.builder().
                        type(MLWorkerReplyType.FINISH).
                        message(result).build())) {
                        log.warn("Cannot offer a reply {}", result);
                    } else {
                        // Remove once got final result
                        removeResultWaiter(repId);
                    }
                } else {
                    // TODO: Currently multiple shot only keeps the newest
                }
            }
        }
    }

    public BlockingQueue<MLWorkerReplyMessage> getResultWaiter(String repId) {
        if (finalMessagePool.containsKey(repId)) return finalMessagePool.get(repId);

        BlockingQueue<MLWorkerReplyMessage> bq = new ArrayBlockingQueue<>(1);
        finalMessagePool.put(repId, bq);
        return bq;
    }

    public void removeResultWaiter(String repId) {
        synchronized (messagePool) {
            messagePool.remove(repId);
        }

        synchronized (finalMessagePool) {
            finalMessagePool.remove(repId);
        }
    }

    public boolean isWorkerConnected(MLWorkerID workerID) {
        return workers.containsKey(workerID.toString());
    }
}
