package ai.giskard.mock;

import ai.giskard.domain.Project;
import ai.giskard.domain.User;

public class ProjectMock {

    public static Project mockProject(User owner) {
        final Project project = new Project();

        project.setOwner(owner);
        project.setName(owner.getLogin());
        project.setKey(owner.getLogin());

        return project;
    }

}
