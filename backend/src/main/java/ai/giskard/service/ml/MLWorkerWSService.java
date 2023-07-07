package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.ml.MLWorkerID;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.cglib.core.Block;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ConcurrentHashMap;

@Service
@RequiredArgsConstructor
public class MLWorkerWSService {
    private final Logger log = LoggerFactory.getLogger(MLWorkerWSService.class.getName());
    private final ApplicationProperties applicationProperties;

    private final HashMap<String, String> workers = new HashMap<String, String>();
    private String potentialInternalWorkerId;

    private ConcurrentHashMap<String, BlockingQueue<String>> messagePool = new ConcurrentHashMap<>();
    private ConcurrentHashMap<String, BlockingQueue<String>> oneShotMessagePool = new ConcurrentHashMap<>();

    public boolean prepareInternalWorker(String uuid) {
        if (potentialInternalWorkerId != null && uuid != potentialInternalWorkerId) return false;

        potentialInternalWorkerId = uuid;
        return true;
    }

    public boolean associateWorker(String id, String uuid) {
        if (workers.get(id) != null && workers.get(id) != uuid) {
            // Duplicated, could be an attacker
            return false;
        }
        // Check for internal worker
        if (id == MLWorkerID.INTERNAL.toString() && this.potentialInternalWorkerId != uuid) {
            // UUID not matched, could be an attacker
            return false;
        }

        workers.put(id, uuid);
        return true;
    }

    public boolean removeWorker(String uuid) {
        if (potentialInternalWorkerId == uuid) {
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
            oneShotMessagePool.remove(repId).offer(result);
            return;
        }
        if (messagePool.containsKey(repId)) {
            BlockingQueue<String> bq = messagePool.get(repId);
            // Only keeps the newest
            if (!bq.isEmpty()) {
                bq.remove();
            }
            bq.offer(result);
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
}
