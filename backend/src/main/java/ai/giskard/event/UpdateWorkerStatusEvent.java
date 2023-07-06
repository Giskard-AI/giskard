package ai.giskard.event;

import org.springframework.context.ApplicationEvent;

public class UpdateWorkerStatusEvent extends ApplicationEvent {
    public UpdateWorkerStatusEvent(Object source) {
        super(source);
    }
}
