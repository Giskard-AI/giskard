package ai.giskard.mock;

import ai.giskard.domain.Feedback;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;

public class FeedbackMock {

    public static Feedback mockFeedback(Project project, User creator) {
        final Feedback feedback = new Feedback();

        feedback.setUser(creator);
        feedback.setProject(project);
        feedback.setUserData(creator.getLogin());
        feedback.setFeedbackType(creator.getLogin());
        feedback.setOriginalData(creator.getLogin());

        return feedback;
    }

}
