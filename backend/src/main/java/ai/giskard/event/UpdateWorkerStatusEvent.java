package ai.giskard.event;

import org.springframework.context.ApplicationEvent;

public class UpdateWorkerStatusEvent extends ApplicationEvent {
    public boolean isConnected;

    public UpdateWorkerStatusEvent(Object source, boolean isConnected) {
        super(source);
        this.isConnected = isConnected;
    }
}
