package ai.giskard.ml;

import java.util.ArrayList;
import java.util.List;

public class MLWorkerReplyAggregator {
    private List<String> replies;
    private int count;

    public MLWorkerReplyAggregator(int fragmentCount) {
        this.replies = new ArrayList<>(Integer.max(1, fragmentCount));
        for (int i = 0; i < fragmentCount; i++) {
            this.replies.add(null);
        }
        this.count = 0;
    }

    public synchronized String addReply(int fragmentIndex, String result) {
        if (this.replies.size() > fragmentIndex) {
            if (this.replies.get(fragmentIndex) == null)
                this.count++;    // First add
            return this.replies.set(fragmentIndex, result);
        }
        throw new IndexOutOfBoundsException();
    }

    public boolean isFinished() {
        return this.count == this.replies.size();
    }

    public String aggregate() {
        return String.join("", this.replies);
    }
}
