package ai.giskard.utils;

import org.springframework.transaction.support.TransactionSynchronization;
import org.springframework.transaction.support.TransactionSynchronizationManager;

public class TransactionUtils {

    /**
     * Schedule an action to be executed after the transaction commit<br />
     * This is useful when the scheduled tasks need to access data that have been modified inside the current transaction
     *
     * @param task The task to be scheduled
     */
    public static void executeAfterTransactionCommits(Runnable task) {
        TransactionSynchronizationManager.registerSynchronization(new TransactionSynchronization() {
            public void afterCommit() {
                task.run();
            }
        });
    }

}
