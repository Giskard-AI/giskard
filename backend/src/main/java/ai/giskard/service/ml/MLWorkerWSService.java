package ai.giskard.service.ml;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.ml.MLWorkerID;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import java.util.HashMap;

@Service
@RequiredArgsConstructor
public class MLWorkerWSService {
    private final Logger log = LoggerFactory.getLogger(MLWorkerWSService.class.getName());
    private final ApplicationProperties applicationProperties;

    private final HashMap<String, String> workers = new HashMap<String, String>();
    private String potentialInternalWorkerId;

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
}
