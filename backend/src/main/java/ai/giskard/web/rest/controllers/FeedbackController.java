package ai.giskard.web.rest.controllers;

import ai.giskard.domain.Feedback;
import ai.giskard.domain.FeedbackReply;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import ai.giskard.repository.FeedbackReplyRepository;
import ai.giskard.repository.FeedbackRepository;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.UserRepository;
import ai.giskard.security.SecurityUtils;
import ai.giskard.service.MailService;
import ai.giskard.web.dto.CreateFeedbackDTO;
import ai.giskard.web.dto.CreateFeedbackReplyDTO;
import ai.giskard.web.dto.FeedbackDTO;
import ai.giskard.web.dto.FeedbackMinimalDTO;
import ai.giskard.web.dto.FeedbackReplyDTO;
import ai.giskard.web.dto.mapper.FeedbackMapper;
import ai.giskard.web.rest.errors.Entity;
import ai.giskard.web.rest.errors.UnauthorizedException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;

import static ai.giskard.service.MailService.FeedbackNotificationType.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/feedbacks")
public class FeedbackController {
    private final FeedbackRepository feedbackRepository;
    private final FeedbackReplyRepository feedbackReplyRepository;
    private final ProjectRepository projectRepository;
    private final UserRepository userRepository;
    private final FeedbackMapper feedbackMapper;
    private final MailService mailService;

    @GetMapping("/all/{projectId}")
    @Transactional
    public List<FeedbackMinimalDTO> getAllFeedbacks(
        @PathVariable("projectId") Long projectId, @AuthenticationPrincipal UserDetails user) {
        List<Feedback> feedbacks;
        if (SecurityUtils.isCurrentUserAdmin()) {
            feedbacks = feedbackRepository.findAllByProjectId(projectId);
        } else {
            Project project = projectRepository.getMandatoryById(projectId);
            Long currentUserId = userRepository.getOneByLogin(user.getUsername()).getId();
            if (project.getOwner().getId().equals(currentUserId)) {
                feedbacks = feedbackRepository.findAllByProjectId(projectId);
            } else {
                feedbacks = feedbackRepository.findAllByProjectIdAndUserId(projectId, currentUserId);
            }
        }
        return feedbackMapper.feedbacksToFeedbackMinimalDTOs(feedbacks);
    }

    @Transactional
    @GetMapping("/{feedbackId}")
    public FeedbackDTO getFeedback(@PathVariable("feedbackId") Long feedbackId) {
        Feedback feedback = feedbackRepository.findOneById(feedbackId);

        String currUserLogin = SecurityUtils.getCurrentAuthenticatedUserLogin();
        if (SecurityUtils.isCurrentUserAdmin() ||
            feedback.getProject().getOwner().getLogin().equals(currUserLogin) ||
            feedback.getUser().getLogin().equals(currUserLogin)
        ) {
            return feedbackMapper.feedbackToFeedbackDTO(feedback);
        } else {
            throw new UnauthorizedException("Read feedback", Entity.FEEDBACK);
        }
    }

    @PostMapping("/{projectId}")
    public ResponseEntity<Void> addFeedback(@PathVariable("projectId") Long projectId, @RequestBody CreateFeedbackDTO dto) {
        Project project = projectRepository.getMandatoryById(projectId);
        String currUserLogin = SecurityUtils.getCurrentAuthenticatedUserLogin();
        if (!SecurityUtils.isCurrentUserAdmin() &&
            !project.getOwner().getLogin().equals(currUserLogin) &&
            project.getGuests().stream().noneMatch(u -> u.getLogin().equals(currUserLogin))) {
            throw new UnauthorizedException("Add feedback", Entity.FEEDBACK);
        }

        User currentUser = userRepository.getOneByLogin(currUserLogin);
        Feedback feedback = feedbackMapper.createFeedbackDTOtoFeedback(dto);
        feedback.setUser(currentUser);
        feedbackRepository.save(feedback);


        mailService.sendFeedbackEmail(project.getOwner(), currentUser, feedback, project, feedback.getFeedbackMessage(), CREATE);
        return new ResponseEntity<>(HttpStatus.OK);
    }

    @PostMapping("/{feedbackId}/reply")
    public ResponseEntity<Void> addFeedbackReply(@PathVariable("feedbackId") Long feedbackId, @RequestBody CreateFeedbackReplyDTO dto) {
        String userLogin = SecurityUtils.getCurrentAuthenticatedUserLogin();
        Feedback feedback = feedbackRepository.findOneById(feedbackId);
        Project project = feedback.getProject();
        if (!SecurityUtils.isCurrentUserAdmin() &&
            !project.getOwner().getLogin().equals(userLogin) &&
            project.getGuests().stream().noneMatch(u -> u.getLogin().equals(userLogin))) {
            throw new UnauthorizedException("Add feedback reply", Entity.FEEDBACK);
        }

        User currentUser = userRepository.getOneByLogin(userLogin);
        FeedbackReply reply = feedbackMapper.createFeedbackReplyDTOtoFeedbackReply(dto);
        reply.setFeedback(feedback);
        reply.setUser(currentUser);
        feedbackReplyRepository.save(reply);

        if (!currentUser.getId().equals(project.getOwner().getId())) {
            mailService.sendFeedbackEmail(project.getOwner(), currentUser, feedback, project, reply.getContent(), COMMENT);
        }
        if (!currentUser.getId().equals(feedback.getUser().getId())) {
            mailService.sendFeedbackEmail(feedback.getUser(), currentUser, feedback, project, reply.getContent(), COMMENT);
        }
        if (reply.getReplyToReply() != null) {
            FeedbackReply originalReply = feedbackReplyRepository.getMandatoryById(reply.getReplyToReply());
            if (!currentUser.getId().equals(originalReply.getUser().getId())) {
                mailService.sendFeedbackEmail(originalReply.getUser(), currentUser, feedback, project, reply.getContent(), REPLY);
            }
        }
        return new ResponseEntity<>(HttpStatus.OK);
    }

    @DeleteMapping("/{feedbackId}")
    public ResponseEntity<Void> deleteFeedback(@PathVariable("feedbackId") long feedbackId) {
        Feedback feedback = feedbackRepository.findOneById(feedbackId);

        Long currUserId = SecurityUtils.getCurrentAuthenticatedUserId();
        if (SecurityUtils.isCurrentUserAdmin() ||
            feedback.getProject().getOwner().getId().equals(currUserId) ||
            feedback.getUser().getId().equals(currUserId)
        ) {
            feedbackRepository.delete(feedback);
            return ResponseEntity.noContent().build();
        } else {
            throw new UnauthorizedException("Delete", Entity.FEEDBACK);
        }
    }


    @GetMapping("/{feedbackId}/replies")
    @Transactional
    public List<FeedbackReplyDTO> getRepliesOfFeedback(@PathVariable("feedbackId") long feedbackId) {
        List<FeedbackReply> replies = new ArrayList<>();
        Feedback feedback = feedbackRepository.findOneById(feedbackId);

        String currUserLogin = SecurityUtils.getCurrentAuthenticatedUserLogin();
        if (SecurityUtils.isCurrentUserAdmin() ||
            feedback.getProject().getOwner().getLogin().equals(currUserLogin) ||
            feedback.getUser().getLogin().equals(currUserLogin)
        ) {
            replies = feedbackReplyRepository.findAllByFeedback(feedback);
        }
        return feedbackMapper.feedbackRepliesToFeedbackReplyDTOs(replies);
    }


    @DeleteMapping("/{feedbackId}/replies/{feedbackReplyId}")
    public ResponseEntity<Void> deleteFeedbackReply(@PathVariable("feedbackId") long feedbackId, @PathVariable("feedbackReplyId") long feedbackReplyId) {
        FeedbackReply feedbackReply = feedbackReplyRepository.findOneById(feedbackReplyId);
        Long currUserId = SecurityUtils.getCurrentAuthenticatedUserId();
        if (SecurityUtils.isCurrentUserAdmin() ||
            feedbackReply.getFeedback().getProject().getOwner().getId().equals(currUserId) ||
            feedbackReply.getUser().getId().equals(currUserId)
        ) {
            List<FeedbackReply> repliesToReply = feedbackReplyRepository.findAllByReplyToReply(feedbackReplyId);
            feedbackReplyRepository.deleteAll(repliesToReply);
            feedbackReplyRepository.delete(feedbackReply);
            return ResponseEntity.noContent().build();
        } else {
            throw new UnauthorizedException("Delete", Entity.FEEDBACK_REPLY);
        }
    }

}
