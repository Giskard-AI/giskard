package ai.giskard.service.ml;

import ai.giskard.ml.MLWorkerID;
import lombok.NonNull;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class MLWorkerWSService {
    private final Logger log = LoggerFactory.getLogger(MLWorkerWSService.class.getName());

    private final ConcurrentHashMap<String, String> workers = new ConcurrentHashMap<>();
    private String potentialInternalWorkerId;

    private ConcurrentHashMap<String, BlockingQueue<String>> messagePool = new ConcurrentHashMap<>();
    private ConcurrentHashMap<String, BlockingQueue<String>> oneShotMessagePool = new ConcurrentHashMap<>();

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

    public void attachResult(String repId, String result) {
        if (oneShotMessagePool.containsKey(repId)) {
            if (!oneShotMessagePool.remove(repId).offer(result)) {
                log.warn("Cannot offer a reply {}", result);
            }
            return;
        }
        if (messagePool.containsKey(repId)) {
            BlockingQueue<String> bq = messagePool.get(repId);
            // Only keeps the newest
            if (!bq.isEmpty()) {
                String removed = bq.remove();
                log.debug("Removed {} because a newer reply arrives.", removed);
            }
            if (!bq.offer(result)) {
                log.warn("Cannot offer a reply {}", result);
            }
        }
    }

    public BlockingQueue<String> getResultWaiter(String repId, boolean isOneShot) {
        BlockingQueue<String> bq = new ArrayBlockingQueue<>(1);
        if (isOneShot)
            oneShotMessagePool.put(repId, bq);
        else
            messagePool.put(repId, bq);
        return bq;
    }

    public void removeResultWaiter(String repId) {
        if (messagePool.containsKey(repId)) {
            messagePool.remove(repId);
            return;
        }

        if (oneShotMessagePool.containsKey(repId)) {
            oneShotMessagePool.remove(repId);
        }
    }

    public boolean isWorkerConnected(MLWorkerID workerID) {
        return workers.containsKey(workerID.toString());
    }
}
