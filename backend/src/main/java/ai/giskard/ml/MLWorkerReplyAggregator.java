package ai.giskard.ml;

import java.util.ArrayList;

public class MLWorkerReplyAggregator {
    private ArrayList<String> replies;
    private int count;

    public MLWorkerReplyAggregator(int fragmentCount) {
        this.replies = new ArrayList<>(Integer.min(1, fragmentCount));
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
        return null;
    }

    public boolean isFinished() {
        return this.count == this.replies.size();
    }

    public String aggregate() {
        return String.join("", this.replies);
    }
}
