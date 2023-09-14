package ai.giskard.service;

import ai.giskard.domain.Feedback;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.RoleRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.AuthoritiesConstants;
import lombok.RequiredArgsConstructor;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Collections;
import java.util.List;

/**
 * Service class for managing users.
 */
@Service
@RequiredArgsConstructor
public class UserDeletionService {

    private final Logger log = LoggerFactory.getLogger(UserDeletionService.class);

    private final UserRepository userRepository;

    private final RoleRepository roleRepository;

    private final ProjectService projectService;

    private final ProjectRepository projectRepository;

    private final FeedbackRepository feedbackRepository;


    private void ensureAnyOtherAdminExists(User user) {
        roleRepository.findByName(AuthoritiesConstants.ADMIN).ifPresent(adminRole -> {
            if (user.getRoles().contains(adminRole) && userRepository.findByRolesNameIn(Collections.singletonList(adminRole.getName())).size() < 2) {
                throw new GiskardRuntimeException("You must have at least one other admin user before disabling or deleting an admin user.");
            }
        });
    }

    /***
     * Tries to delete a user.
     * User cannot be the only admin (ie there must be one admin left after disabling)
     * @param login
     */
    @Transactional
    public void deleteUser(String login) {
        userRepository.findOneWithRolesByLogin(login).ifPresent(user -> {
            ensureAnyOtherAdminExists(user);

            deleteUserOwnedProjects(user);

            setUserFeedbacksToDeletedUser(user);

            user.getProjects().forEach(project -> project.getGuests().remove(user));

            userRepository.delete(user);
        });
    }

    private void setUserFeedbacksToDeletedUser(User user) {
        List<Feedback> userFeedbacks = feedbackRepository.findAllByUser(user);
        if (!userFeedbacks.isEmpty()) {
            userFeedbacks.forEach(feedback -> feedback.setUser(null));
            feedbackRepository.saveAll(userFeedbacks);
        }
    }

    private void deleteUserOwnedProjects(User user) {
        List<Project> ownedProjects = projectRepository.getProjectsByOwner(user);
        if (!ownedProjects.isEmpty()) {
            ownedProjects.forEach(project -> projectService.delete(project.getId()));
        }
    }

    /***
     * Tries to disable a user.
     * User cannot be the only admin (ie there must be one admin left after disabling)
     * @param login
     */
    public void disableUser(String login) {
        userRepository.findOneWithRolesByLogin(login).ifPresent(user -> {
            ensureAnyOtherAdminExists(user);

            user.setEnabled(false);
            userRepository.save(user);
        });
    }

    public void enableUser(String login) {
        userRepository
            .findOneByLogin(login)
            .ifPresentOrElse(user -> {
                    user.setEnabled(true);
                    userRepository.save(user);
                    log.info("Enable user : {}", user);
                },
                () -> log.warn("Cannot enable user because its login wasn't found : {}", login));
    }

}
