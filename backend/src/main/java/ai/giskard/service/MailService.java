package ai.giskard.service;

import ai.giskard.config.ApplicationProperties;
import ai.giskard.domain.Feedback;
import ai.giskard.domain.Project;
import ai.giskard.domain.User;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.context.MessageSource;
import org.springframework.mail.MailException;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.thymeleaf.context.Context;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import org.thymeleaf.spring6.SpringTemplateEngine;

import java.nio.charset.StandardCharsets;
import java.util.Locale;

/**
 * Service for sending emails.
 * <p>
 * We use the {@link Async} annotation to send emails asynchronously.
 */
@Service
public class MailService {
    public enum FeedbackNotificationType {
        CREATE, COMMENT, REPLY
    }

    private final Logger log = LoggerFactory.getLogger(MailService.class);

    private static final String USER = "user";

    private static final String BASE_URL = "baseUrl";

    private final ApplicationProperties applicationProperties;

    private final JavaMailSender javaMailSender;

    private final MessageSource messageSource;

    private final SpringTemplateEngine templateEngine;

    public MailService(
        ApplicationProperties applicationProperties,
        JavaMailSender javaMailSender,
        MessageSource messageSource,
        SpringTemplateEngine templateEngine
    ) {
        this.applicationProperties = applicationProperties;
        this.javaMailSender = javaMailSender;
        this.messageSource = messageSource;
        this.templateEngine = templateEngine;
    }

    //@Async
    public void sendEmail(String to, String subject, String content, boolean isMultipart, boolean isHtml) {
        log.debug(
            "Send email[multipart '{}' and html '{}'] to '{}' with subject '{}' and content={}",
            isMultipart,
            isHtml,
            to,
            subject,
            content
        );

        // Prepare message using a Spring helper
        MimeMessage mimeMessage = javaMailSender.createMimeMessage();
        try {
            MimeMessageHelper message = new MimeMessageHelper(mimeMessage, isMultipart, StandardCharsets.UTF_8.name());
            message.setTo(to);
            message.setFrom(applicationProperties.getEmailFrom());
            message.setSubject(subject);
            message.setText(content, isHtml);
            javaMailSender.send(mimeMessage);
            log.debug("Sent email to User '{}'", to);
        } catch (MailException | MessagingException e) {
            log.warn("Email could not be sent to user '{}'", to, e);
        }
    }

    @Async
    public void sendEmailFromTemplate(User user, String templateName, String titleKey) {
        if (user.getEmail() == null) {
            log.debug("Email doesn't exist for user '{}'", user.getLogin());
            return;
        }
        Context context = new Context();
        context.setVariable(USER, user);
        context.setVariable(BASE_URL, applicationProperties.getMailBaseUrl());
        String content = templateEngine.process(templateName, context);
        String subject = messageSource.getMessage(titleKey, null, Locale.ENGLISH);
        sendEmail(user.getEmail(), subject, content, false, true);
    }

    //@Async
    public void sendUserSignupInvitationEmail(String currentEmail, String email, String inviteLink) {
        log.debug("Sending user invitation email to '{}'", email);
        Context context = new Context();
        context.setVariable("email", email);
        context.setVariable("inviter", currentEmail);
        context.setVariable("inviteLink", inviteLink);
        context.setVariable(BASE_URL, applicationProperties.getMailBaseUrl());

        String content = templateEngine.process("mail/inviteUser", context);
        sendEmail(email, "Giskard invitation", content, false, true);
    }

    @Async
    public void sendActivationEmail(User user) {
        log.debug("Sending activation email to '{}'", user.getEmail());
        sendEmailFromTemplate(user, "mail/activationEmail", "email.activation.title");
    }

    @Async
    public void sendCreationEmail(User user) {
        log.debug("Sending creation email to '{}'", user.getEmail());
        sendEmailFromTemplate(user, "mail/creationEmail", "email.activation.title");
    }

    @Async
    public void sendPasswordResetMail(User user) {
        log.debug("Sending password reset email to '{}'", user.getEmail());
        sendEmailFromTemplate(user, "mail/passwordResetEmail", "email.reset.title");
    }

    public void sendFeedbackEmail(
        User projectOwner, User commenter, Feedback feedback, Project project, String message, FeedbackNotificationType type
    ) {
        Context context = new Context();

        context.setVariable("type", type);
        context.setVariable("commenter", commenter.getDisplayNameOrLogin());
        context.setVariable("projectName", project.getName());
        context.setVariable("projectId", feedback.getProject().getId());
        context.setVariable("feedbackId", feedback.getId());
        context.setVariable("message", message);
        context.setVariable(BASE_URL, applicationProperties.getMailBaseUrl());

        String content = templateEngine.process("mail/feedbackEmail", context);

        String subject;
        switch (type) {
            case CREATE:
                subject = "You received a feedback";
                break;
            case REPLY:
                subject = "You received a reply";
                break;
            case COMMENT:
                subject = "New comment on feedback";
                break;
            default:
                subject = "New feedback activity";
        }
        sendEmail(projectOwner.getEmail(), subject, content, false, true);
    }
}
