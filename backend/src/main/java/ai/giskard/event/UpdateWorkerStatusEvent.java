package ai.giskard.event;

import org.springframework.context.ApplicationEvent;

public class UpdateWorkerStatusEvent extends ApplicationEvent {
    private final boolean isConnected;
    public UpdateWorkerStatusEvent(Object source, boolean isConnected) {
        super(source);
        this.isConnected = isConnected;
    }

    public boolean isConnected() {
        return isConnected;
    }
}
