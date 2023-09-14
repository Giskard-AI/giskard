package ai.giskard.web.dto.mapper;

import ai.giskard.domain.Feedback;
import ai.giskard.domain.FeedbackReply;
import ai.giskard.domain.User;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.web.dto.CreateFeedbackDTO;
import ai.giskard.web.dto.CreateFeedbackReplyDTO;
import ai.giskard.web.dto.FeedbackDTO;
import ai.giskard.web.dto.FeedbackMinimalDTO;
import ai.giskard.web.dto.FeedbackReplyDTO;
import ai.giskard.web.dto.user.UserMinimalDTO;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import jakarta.annotation.processing.Generated;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Generated(
    value = "org.mapstruct.ap.MappingProcessor",
    date = "2023-08-17T12:14:38+0200",
    comments = "version: 1.5.3.Final, compiler: javac, environment: Java 17.0.8 (Eclipse Adoptium)"
)
@Component
public class FeedbackMapperImpl implements FeedbackMapper {

    @Autowired
    private GiskardMapper giskardMapper;
    @Autowired
    private DatasetRepository datasetRepository;
    @Autowired
    private ModelRepository modelRepository;
    @Autowired
    private ProjectRepository projectRepository;

    @Override
    public FeedbackDTO feedbackToFeedbackDTO(Feedback feedback) {
        if ( feedback == null ) {
            return null;
        }

        FeedbackDTO feedbackDTO = new FeedbackDTO();

        feedbackDTO.setId( feedback.getId() );
        feedbackDTO.setProject( giskardMapper.projectToProjectDTO( feedback.getProject() ) );
        feedbackDTO.setModel( giskardMapper.modelToModelDTO( feedback.getModel() ) );
        feedbackDTO.setDataset( giskardMapper.datasetToDatasetDTO( feedback.getDataset() ) );
        feedbackDTO.setUser( userToUserMinimalDTO( feedback.getUser() ) );
        feedbackDTO.setFeedbackReplies( feedbackReplySetToFeedbackReplyDTOSet( feedback.getFeedbackReplies() ) );
        feedbackDTO.setTargetFeature( feedback.getTargetFeature() );
        feedbackDTO.setCreatedOn( feedback.getCreatedOn() );
        feedbackDTO.setFeedbackType( feedback.getFeedbackType() );
        feedbackDTO.setFeatureName( feedback.getFeatureName() );
        feedbackDTO.setFeatureValue( feedback.getFeatureValue() );
        feedbackDTO.setFeedbackChoice( feedback.getFeedbackChoice() );
        feedbackDTO.setFeedbackMessage( feedback.getFeedbackMessage() );
        feedbackDTO.setUserData( feedback.getUserData() );
        feedbackDTO.setOriginalData( feedback.getOriginalData() );

        return feedbackDTO;
    }

    @Override
    public FeedbackMinimalDTO feedbackToFeedbackMinimalDTO(Feedback feedback) {
        if ( feedback == null ) {
            return null;
        }

        FeedbackMinimalDTO feedbackMinimalDTO = new FeedbackMinimalDTO();

        feedbackMinimalDTO.setUserLogin( feedbackUserLogin( feedback ) );
        feedbackMinimalDTO.setModelName( feedbackModelName( feedback ) );
        feedbackMinimalDTO.setDatasetName( feedbackDatasetName( feedback ) );
        feedbackMinimalDTO.setModelId( feedbackModelId( feedback ) );
        feedbackMinimalDTO.setDatasetId( feedbackDatasetId( feedback ) );
        feedbackMinimalDTO.setId( feedback.getId() );
        feedbackMinimalDTO.setCreatedOn( feedback.getCreatedOn() );
        feedbackMinimalDTO.setFeedbackType( feedback.getFeedbackType() );
        feedbackMinimalDTO.setFeatureName( feedback.getFeatureName() );
        feedbackMinimalDTO.setFeatureValue( feedback.getFeatureValue() );
        feedbackMinimalDTO.setFeedbackChoice( feedback.getFeedbackChoice() );
        feedbackMinimalDTO.setFeedbackMessage( feedback.getFeedbackMessage() );

        return feedbackMinimalDTO;
    }

    @Override
    public Feedback createFeedbackDTOtoFeedback(CreateFeedbackDTO dto) {
        if ( dto == null ) {
            return null;
        }

        Feedback feedback = new Feedback();

        feedback.setProject( projectRepository.findOneByNullableId( dto.getProjectId() ) );
        feedback.setModel( modelRepository.findOneByNullableId( dto.getModelId() ) );
        feedback.setDataset( datasetRepository.findOneByNullableId( dto.getDatasetId() ) );
        feedback.setTargetFeature( dto.getTargetFeature() );
        feedback.setFeedbackType( dto.getFeedbackType() );
        feedback.setFeatureName( dto.getFeatureName() );
        feedback.setFeatureValue( dto.getFeatureValue() );
        feedback.setFeedbackChoice( dto.getFeedbackChoice() );
        feedback.setFeedbackMessage( dto.getFeedbackMessage() );
        feedback.setUserData( dto.getUserData() );
        feedback.setOriginalData( dto.getOriginalData() );

        return feedback;
    }

    @Override
    public FeedbackReply createFeedbackReplyDTOtoFeedbackReply(CreateFeedbackReplyDTO dto) {
        if ( dto == null ) {
            return null;
        }

        FeedbackReply feedbackReply = new FeedbackReply();

        if ( dto.getReplyToReply() != null ) {
            feedbackReply.setReplyToReply( dto.getReplyToReply().longValue() );
        }
        feedbackReply.setContent( dto.getContent() );

        return feedbackReply;
    }

    @Override
    public FeedbackReplyDTO feedbackReplyToFeedbackReplyDTO(FeedbackReply feedbackReply) {
        if ( feedbackReply == null ) {
            return null;
        }

        FeedbackReplyDTO feedbackReplyDTO = new FeedbackReplyDTO();

        feedbackReplyDTO.setFeedbackId( feedbackReplyFeedbackId( feedbackReply ) );
        feedbackReplyDTO.setId( feedbackReply.getId() );
        feedbackReplyDTO.setUser( userToUserMinimalDTO( feedbackReply.getUser() ) );
        feedbackReplyDTO.setReplyToReply( feedbackReply.getReplyToReply() );
        feedbackReplyDTO.setContent( feedbackReply.getContent() );
        feedbackReplyDTO.setCreatedOn( feedbackReply.getCreatedOn() );

        return feedbackReplyDTO;
    }

    @Override
    public List<FeedbackMinimalDTO> feedbacksToFeedbackMinimalDTOs(List<Feedback> feedbacks) {
        if ( feedbacks == null ) {
            return null;
        }

        List<FeedbackMinimalDTO> list = new ArrayList<FeedbackMinimalDTO>( feedbacks.size() );
        for ( Feedback feedback : feedbacks ) {
            list.add( feedbackToFeedbackMinimalDTO( feedback ) );
        }

        return list;
    }

    @Override
    public List<FeedbackReplyDTO> feedbackRepliesToFeedbackReplyDTOs(List<FeedbackReply> feedbackReplies) {
        if ( feedbackReplies == null ) {
            return null;
        }

        List<FeedbackReplyDTO> list = new ArrayList<FeedbackReplyDTO>( feedbackReplies.size() );
        for ( FeedbackReply feedbackReply : feedbackReplies ) {
            list.add( feedbackReplyToFeedbackReplyDTO( feedbackReply ) );
        }

        return list;
    }

    protected UserMinimalDTO userToUserMinimalDTO(User user) {
        if ( user == null ) {
            return null;
        }

        UserMinimalDTO userMinimalDTO = new UserMinimalDTO();

        userMinimalDTO.id = user.getId();
        userMinimalDTO.login = user.getLogin();
        userMinimalDTO.displayName = user.getDisplayName();

        return userMinimalDTO;
    }

    protected Set<FeedbackReplyDTO> feedbackReplySetToFeedbackReplyDTOSet(Set<FeedbackReply> set) {
        if ( set == null ) {
            return null;
        }

        Set<FeedbackReplyDTO> set1 = new LinkedHashSet<FeedbackReplyDTO>( Math.max( (int) ( set.size() / .75f ) + 1, 16 ) );
        for ( FeedbackReply feedbackReply : set ) {
            set1.add( feedbackReplyToFeedbackReplyDTO( feedbackReply ) );
        }

        return set1;
    }

    private String feedbackUserLogin(Feedback feedback) {
        if ( feedback == null ) {
            return null;
        }
        User user = feedback.getUser();
        if ( user == null ) {
            return null;
        }
        String login = user.getLogin();
        if ( login == null ) {
            return null;
        }
        return login;
    }

    private String feedbackModelName(Feedback feedback) {
        if ( feedback == null ) {
            return null;
        }
        ProjectModel model = feedback.getModel();
        if ( model == null ) {
            return null;
        }
        String name = model.getName();
        if ( name == null ) {
            return null;
        }
        return name;
    }

    private String feedbackDatasetName(Feedback feedback) {
        if ( feedback == null ) {
            return null;
        }
        Dataset dataset = feedback.getDataset();
        if ( dataset == null ) {
            return null;
        }
        String name = dataset.getName();
        if ( name == null ) {
            return null;
        }
        return name;
    }

    private UUID feedbackModelId(Feedback feedback) {
        if ( feedback == null ) {
            return null;
        }
        ProjectModel model = feedback.getModel();
        if ( model == null ) {
            return null;
        }
        UUID id = model.getId();
        if ( id == null ) {
            return null;
        }
        return id;
    }

    private UUID feedbackDatasetId(Feedback feedback) {
        if ( feedback == null ) {
            return null;
        }
        Dataset dataset = feedback.getDataset();
        if ( dataset == null ) {
            return null;
        }
        UUID id = dataset.getId();
        if ( id == null ) {
            return null;
        }
        return id;
    }

    private Long feedbackReplyFeedbackId(FeedbackReply feedbackReply) {
        if ( feedbackReply == null ) {
            return null;
        }
        Feedback feedback = feedbackReply.getFeedback();
        if ( feedback == null ) {
            return null;
        }
        Long id = feedback.getId();
        if ( id == null ) {
            return null;
        }
        return id;
    }
}
