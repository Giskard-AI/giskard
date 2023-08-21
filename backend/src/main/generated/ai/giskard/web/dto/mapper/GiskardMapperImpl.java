package ai.giskard.web.dto.mapper;

import ai.giskard.domain.ColumnType;
import ai.giskard.domain.Feedback;
import ai.giskard.domain.FunctionArgument;
import ai.giskard.domain.Project;
import ai.giskard.domain.SlicingFunction;
import ai.giskard.domain.TestFunction;
import ai.giskard.domain.TransformationFunction;
import ai.giskard.domain.User;
import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.FunctionInput;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.domain.ml.SuiteTest;
import ai.giskard.domain.ml.SuiteTestExecution;
import ai.giskard.domain.ml.TestSuite;
import ai.giskard.domain.ml.TestSuiteExecution;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.web.dto.FunctionInputDTO;
import ai.giskard.web.dto.ModelMetadataDTO;
import ai.giskard.web.dto.PrepareDeleteDTO;
import ai.giskard.web.dto.SlicingFunctionDTO;
import ai.giskard.web.dto.SuiteTestDTO;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.TestSuiteDTO;
import ai.giskard.web.dto.TransformationFunctionDTO;
import ai.giskard.web.dto.ml.DatasetDTO;
import ai.giskard.web.dto.ml.InspectionDTO;
import ai.giskard.web.dto.ml.ModelDTO;
import ai.giskard.web.dto.ml.ProjectDTO;
import ai.giskard.web.dto.ml.ProjectPostDTO;
import ai.giskard.web.dto.ml.SuiteTestExecutionDTO;
import ai.giskard.web.dto.ml.TestResultMessageDTO;
import ai.giskard.web.dto.ml.TestSuiteExecutionDTO;
import ai.giskard.web.dto.user.AdminUserDTO;
import ai.giskard.web.dto.user.UserDTO;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import javax.annotation.processing.Generated;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

@Generated(
    value = "org.mapstruct.ap.MappingProcessor",
    date = "2023-08-17T12:14:38+0200",
    comments = "version: 1.5.3.Final, compiler: javac, environment: Java 17.0.8 (Eclipse Adoptium)"
)
@Component
public class GiskardMapperImpl implements GiskardMapper {

    @Autowired
    private ProjectRepository projectRepository;
    @Autowired
    private TestFunctionRepository testFunctionRepository;

    @Override
    public void updateProjectFromDto(ProjectPostDTO dto, Project entity) {
        if ( dto == null ) {
            return;
        }

        if ( dto.getKey() != null ) {
            entity.setKey( dto.getKey() );
        }
        if ( dto.getName() != null ) {
            entity.setName( dto.getName() );
        }
        if ( dto.getDescription() != null ) {
            entity.setDescription( dto.getDescription() );
        }
    }

    @Override
    public Project projectPostDTOToProject(ProjectPostDTO projectPostDto) {
        if ( projectPostDto == null ) {
            return null;
        }

        Project project = new Project();

        project.setKey( projectPostDto.getKey() );
        project.setName( projectPostDto.getName() );
        project.setDescription( projectPostDto.getDescription() );

        return project;
    }

    @Override
    public ProjectPostDTO projectToProjectPostDTO(Project project) {
        if ( project == null ) {
            return null;
        }

        ProjectPostDTO projectPostDTO = new ProjectPostDTO();

        projectPostDTO.setId( project.getId() );
        projectPostDTO.setName( project.getName() );
        projectPostDTO.setKey( project.getKey() );
        projectPostDTO.setDescription( project.getDescription() );

        return projectPostDTO;
    }

    @Override
    public ProjectDTO projectToProjectDTO(Project project) {
        if ( project == null ) {
            return null;
        }

        ProjectDTO projectDTO = new ProjectDTO();

        projectDTO.setId( project.getId() );
        projectDTO.setName( project.getName() );
        projectDTO.setOwner( userToUserDTO( project.getOwner() ) );
        projectDTO.setKey( project.getKey() );
        projectDTO.setDescription( project.getDescription() );
        projectDTO.setGuests( userSetToUserDTOList( project.getGuests() ) );
        projectDTO.setCreatedDate( project.getCreatedDate() );
        projectDTO.setMlWorkerType( project.getMlWorkerType() );

        return projectDTO;
    }

    @Override
    public List<ProjectDTO> projectsToProjectDTOs(List<Project> projects) {
        if ( projects == null ) {
            return null;
        }

        List<ProjectDTO> list = new ArrayList<ProjectDTO>( projects.size() );
        for ( Project project : projects ) {
            list.add( projectToProjectDTO( project ) );
        }

        return list;
    }

    @Override
    public List<ModelDTO> modelsToModelDTOs(List<ProjectModel> models) {
        if ( models == null ) {
            return null;
        }

        List<ModelDTO> list = new ArrayList<ModelDTO>( models.size() );
        for ( ProjectModel projectModel : models ) {
            list.add( modelToModelDTO( projectModel ) );
        }

        return list;
    }

    @Override
    public ModelDTO modelToModelDTO(ProjectModel model) {
        if ( model == null ) {
            return null;
        }

        ModelDTO modelDTO = new ModelDTO();

        List<String> list = model.getClassificationLabels();
        if ( list != null ) {
            modelDTO.setClassificationLabels( new ArrayList<String>( list ) );
        }
        List<String> list1 = model.getFeatureNames();
        if ( list1 != null ) {
            modelDTO.setFeatureNames( new ArrayList<String>( list1 ) );
        }
        modelDTO.setLanguageVersion( model.getLanguageVersion() );
        modelDTO.setLanguage( model.getLanguage() );
        modelDTO.setModelType( model.getModelType() );
        modelDTO.setThreshold( model.getThreshold() );
        modelDTO.setClassificationLabelsDtype( model.getClassificationLabelsDtype() );
        modelDTO.setId( model.getId() );
        modelDTO.setProject( projectToProjectDTO( model.getProject() ) );
        modelDTO.setName( model.getName() );
        modelDTO.setCreatedDate( model.getCreatedDate() );
        modelDTO.setSize( model.getSize() );

        return modelDTO;
    }

    @Override
    public List<DatasetDTO> datasetsToDatasetDTOs(List<Dataset> datasets) {
        if ( datasets == null ) {
            return null;
        }

        List<DatasetDTO> list = new ArrayList<DatasetDTO>( datasets.size() );
        for ( Dataset dataset : datasets ) {
            list.add( datasetToDatasetDTO( dataset ) );
        }

        return list;
    }

    @Override
    public DatasetDTO datasetToDatasetDTO(Dataset dataset) {
        if ( dataset == null ) {
            return null;
        }

        DatasetDTO datasetDTO = new DatasetDTO();

        Map<String, ColumnType> map = dataset.getColumnTypes();
        if ( map != null ) {
            datasetDTO.setColumnTypes( new LinkedHashMap<String, ColumnType>( map ) );
        }
        datasetDTO.setTarget( dataset.getTarget() );
        datasetDTO.setProject( projectToProjectDTO( dataset.getProject() ) );
        datasetDTO.setId( dataset.getId() );
        datasetDTO.setName( dataset.getName() );
        Map<String, String> map1 = dataset.getColumnDtypes();
        if ( map1 != null ) {
            datasetDTO.setColumnDtypes( new LinkedHashMap<String, String>( map1 ) );
        }
        if ( dataset.getOriginalSizeBytes() != null ) {
            datasetDTO.setOriginalSizeBytes( dataset.getOriginalSizeBytes().intValue() );
        }
        if ( dataset.getCompressedSizeBytes() != null ) {
            datasetDTO.setCompressedSizeBytes( dataset.getCompressedSizeBytes().intValue() );
        }
        datasetDTO.setNumberOfRows( dataset.getNumberOfRows() );
        Map<String, List<String>> map2 = dataset.getCategoryFeatures();
        if ( map2 != null ) {
            datasetDTO.setCategoryFeatures( new LinkedHashMap<String, List<String>>( map2 ) );
        }
        datasetDTO.setCreatedDate( dataset.getCreatedDate() );

        return datasetDTO;
    }

    @Override
    public UserDTO userToUserDTO(User user) {
        if ( user == null ) {
            return null;
        }

        UserDTO userDTO = new UserDTO();

        userDTO.setId( user.getId() );
        userDTO.setLogin( user.getLogin() );
        userDTO.setDisplayName( user.getDisplayName() );
        userDTO.setRoles( roleNames( user.getRoles() ) );

        return userDTO;
    }

    @Override
    public InspectionDTO toDTO(Inspection inspection) {
        if ( inspection == null ) {
            return null;
        }

        InspectionDTO inspectionDTO = new InspectionDTO();

        inspectionDTO.setId( inspection.getId() );
        inspectionDTO.setDataset( datasetToDatasetDTO( inspection.getDataset() ) );
        inspectionDTO.setModel( modelToModelDTO( inspection.getModel() ) );
        inspectionDTO.setName( inspection.getName() );
        inspectionDTO.setSample( inspection.isSample() );
        inspectionDTO.setCreatedDate( inspection.getCreatedDate() );

        return inspectionDTO;
    }

    @Override
    public List<InspectionDTO> inspectionsToInspectionDTOs(List<Inspection> inspections) {
        if ( inspections == null ) {
            return null;
        }

        List<InspectionDTO> list = new ArrayList<InspectionDTO>( inspections.size() );
        for ( Inspection inspection : inspections ) {
            list.add( toDTO( inspection ) );
        }

        return list;
    }

    @Override
    public AdminUserDTO userToAdminUserDTO(User user) {
        if ( user == null ) {
            return null;
        }

        AdminUserDTO adminUserDTO = new AdminUserDTO();

        adminUserDTO.setId( user.getId() );
        adminUserDTO.setLogin( user.getLogin() );
        adminUserDTO.setDisplayName( user.getDisplayName() );
        adminUserDTO.setEmail( user.getEmail() );
        adminUserDTO.setEnabled( user.isEnabled() );
        adminUserDTO.setActivated( user.isActivated() );
        adminUserDTO.setCreatedBy( user.getCreatedBy() );
        adminUserDTO.setCreatedDate( user.getCreatedDate() );
        adminUserDTO.setLastModifiedBy( user.getLastModifiedBy() );
        adminUserDTO.setLastModifiedDate( user.getLastModifiedDate() );
        adminUserDTO.setRoles( roleNames( user.getRoles() ) );

        return adminUserDTO;
    }

    @Override
    public User adminUserDTOtoUser(AdminUserDTO dto) {
        if ( dto == null ) {
            return null;
        }

        User user = new User();

        user.setCreatedBy( dto.getCreatedBy() );
        user.setCreatedDate( dto.getCreatedDate() );
        user.setLastModifiedBy( dto.getLastModifiedBy() );
        user.setLastModifiedDate( dto.getLastModifiedDate() );
        user.setLogin( dto.getLogin() );
        user.setId( dto.getId() );
        user.setDisplayName( dto.getDisplayName() );
        user.setEmail( dto.getEmail() );
        user.setActivated( dto.isActivated() );
        user.setEnabled( dto.isEnabled() );
        user.setRoles( stringSetToRoleSet( dto.getRoles() ) );

        return user;
    }

    @Override
    public ModelMetadataDTO modelToModelMetadataDTO(ProjectModel model) {
        if ( model == null ) {
            return null;
        }

        ModelMetadataDTO.ModelMetadataDTOBuilder modelMetadataDTO = ModelMetadataDTO.builder();

        List<String> list = model.getClassificationLabels();
        if ( list != null ) {
            modelMetadataDTO.classificationLabels( new ArrayList<String>( list ) );
        }
        List<String> list1 = model.getFeatureNames();
        if ( list1 != null ) {
            modelMetadataDTO.featureNames( new ArrayList<String>( list1 ) );
        }
        modelMetadataDTO.id( model.getId() );
        modelMetadataDTO.modelType( model.getModelType() );
        modelMetadataDTO.threshold( model.getThreshold() );

        return modelMetadataDTO.build();
    }

    @Override
    public ProjectModel fromDTO(ModelDTO dto) {
        if ( dto == null ) {
            return null;
        }

        ProjectModel projectModel = new ProjectModel();

        projectModel.setProject( projectRepository.findOneByNullableId( dto.getProjectId() ) );
        projectModel.setId( dto.getId() );
        projectModel.setName( dto.getName() );
        projectModel.setSize( dto.getSize() );
        projectModel.setLanguageVersion( dto.getLanguageVersion() );
        projectModel.setLanguage( dto.getLanguage() );
        projectModel.setModelType( dto.getModelType() );
        projectModel.setThreshold( dto.getThreshold() );
        List<String> list = dto.getFeatureNames();
        if ( list != null ) {
            projectModel.setFeatureNames( new ArrayList<String>( list ) );
        }
        List<String> list1 = dto.getClassificationLabels();
        if ( list1 != null ) {
            projectModel.setClassificationLabels( new ArrayList<String>( list1 ) );
        }
        projectModel.setClassificationLabelsDtype( dto.getClassificationLabelsDtype() );

        return projectModel;
    }

    @Override
    public Dataset fromDTO(DatasetDTO dto) {
        if ( dto == null ) {
            return null;
        }

        Dataset dataset = new Dataset();

        Map<String, ColumnType> map = dto.getColumnTypes();
        if ( map != null ) {
            dataset.setColumnTypes( new LinkedHashMap<String, ColumnType>( map ) );
        }
        dataset.setId( dto.getId() );
        dataset.setName( dto.getName() );
        Map<String, String> map1 = dto.getColumnDtypes();
        if ( map1 != null ) {
            dataset.setColumnDtypes( new LinkedHashMap<String, String>( map1 ) );
        }
        dataset.setTarget( dto.getTarget() );
        dataset.setOriginalSizeBytes( (long) dto.getOriginalSizeBytes() );
        dataset.setCompressedSizeBytes( (long) dto.getCompressedSizeBytes() );
        dataset.setNumberOfRows( dto.getNumberOfRows() );
        Map<String, List<String>> map2 = dto.getCategoryFeatures();
        if ( map2 != null ) {
            dataset.setCategoryFeatures( new LinkedHashMap<String, List<String>>( map2 ) );
        }

        return dataset;
    }

    @Override
    public PrepareDeleteDTO.LightFeedback toDTO(Feedback obj) {
        if ( obj == null ) {
            return null;
        }

        PrepareDeleteDTO.LightFeedback lightFeedback = new PrepareDeleteDTO.LightFeedback();

        lightFeedback.message = obj.getFeedbackMessage();
        Long id = objProjectId( obj );
        if ( id != null ) {
            lightFeedback.projectId = id;
        }
        if ( obj.getId() != null ) {
            lightFeedback.id = obj.getId();
        }

        return lightFeedback;
    }

    @Override
    public List<PrepareDeleteDTO.LightFeedback> toLightFeedbacks(List<Feedback> obj) {
        if ( obj == null ) {
            return null;
        }

        List<PrepareDeleteDTO.LightFeedback> list = new ArrayList<PrepareDeleteDTO.LightFeedback>( obj.size() );
        for ( Feedback feedback : obj ) {
            list.add( toDTO( feedback ) );
        }

        return list;
    }

    @Override
    public TestSuite fromDTO(TestSuiteDTO dto) {
        if ( dto == null ) {
            return null;
        }

        TestSuite testSuite = new TestSuite();

        testSuite.setProject( projectRepository.getOneByKey( dto.getProjectKey() ) );
        testSuite.setName( dto.getName() );
        testSuite.setFunctionInputs( functionInputDTOListToFunctionInputList( dto.getFunctionInputs() ) );
        testSuite.setTests( suiteTestDTOListToSuiteTestList( dto.getTests() ) );

        afterMapping( testSuite );

        return testSuite;
    }

    @Override
    public SuiteTest fromDTO(SuiteTestDTO dto) {
        if ( dto == null ) {
            return null;
        }

        SuiteTest suiteTest = new SuiteTest();

        suiteTest.setTestFunction( testFunctionRepository.findOneByNullableId( dto.getTestUuid() ) );
        suiteTest.setFunctionInputs( map( dto.getFunctionInputs() ) );

        return suiteTest;
    }

    @Override
    public FunctionInput fromDTO(FunctionInputDTO dto) {
        if ( dto == null ) {
            return null;
        }

        FunctionInput functionInput = new FunctionInput();

        functionInput.setAlias( dto.isAlias() );
        functionInput.setName( dto.getName() );
        functionInput.setType( dto.getType() );
        functionInput.setValue( dto.getValue() );
        functionInput.setParams( functionInputDTOListToFunctionInputList( dto.getParams() ) );

        return functionInput;
    }

    @Override
    public FunctionInputDTO toDTO(FunctionInput obj) {
        if ( obj == null ) {
            return null;
        }

        FunctionInputDTO functionInputDTO = new FunctionInputDTO();

        functionInputDTO.setName( obj.getName() );
        functionInputDTO.setValue( obj.getValue() );
        functionInputDTO.setType( obj.getType() );
        functionInputDTO.setAlias( obj.isAlias() );
        functionInputDTO.setParams( functionInputListToFunctionInputDTOList( obj.getParams() ) );

        return functionInputDTO;
    }

    @Override
    public List<TestSuiteDTO> toDTO(List<TestSuite> suites) {
        if ( suites == null ) {
            return null;
        }

        List<TestSuiteDTO> list = new ArrayList<TestSuiteDTO>( suites.size() );
        for ( TestSuite testSuite : suites ) {
            list.add( toDTO( testSuite ) );
        }

        return list;
    }

    @Override
    public TestSuiteDTO toDTO(TestSuite suite) {
        if ( suite == null ) {
            return null;
        }

        TestSuiteDTO testSuiteDTO = new TestSuiteDTO();

        testSuiteDTO.setProjectKey( suiteProjectKey( suite ) );
        testSuiteDTO.setId( suite.getId() );
        testSuiteDTO.setName( suite.getName() );
        testSuiteDTO.setFunctionInputs( functionInputListToFunctionInputDTOList( suite.getFunctionInputs() ) );
        testSuiteDTO.setTests( suiteTestListToSuiteTestDTOList( suite.getTests() ) );

        return testSuiteDTO;
    }

    @Override
    public SuiteTestDTO toDTO(SuiteTest dto) {
        if ( dto == null ) {
            return null;
        }

        SuiteTestDTO suiteTestDTO = new SuiteTestDTO();

        suiteTestDTO.setTestUuid( dtoTestFunctionUuid( dto ) );
        suiteTestDTO.setTest( toDTO( dto.getTestFunction() ) );
        if ( dto.getId() != null ) {
            suiteTestDTO.setId( dto.getId() );
        }
        suiteTestDTO.setFunctionInputs( map( dto.getFunctionInputs() ) );

        return suiteTestDTO;
    }

    @Override
    public TestSuiteExecutionDTO toDTO(TestSuiteExecution save) {
        if ( save == null ) {
            return null;
        }

        TestSuiteExecutionDTO testSuiteExecutionDTO = new TestSuiteExecutionDTO();

        testSuiteExecutionDTO.setSuiteId( saveSuiteId( save ) );
        testSuiteExecutionDTO.setId( save.getId() );
        testSuiteExecutionDTO.setInputs( functionInputListToFunctionInputDTOList( save.getInputs() ) );
        testSuiteExecutionDTO.setResult( save.getResult() );
        testSuiteExecutionDTO.setMessage( save.getMessage() );
        testSuiteExecutionDTO.setLogs( save.getLogs() );
        testSuiteExecutionDTO.setResults( suiteTestExecutionListToSuiteTestExecutionDTOList( save.getResults() ) );
        testSuiteExecutionDTO.setExecutionDate( save.getExecutionDate() );
        testSuiteExecutionDTO.setCompletionDate( save.getCompletionDate() );

        return testSuiteExecutionDTO;
    }

    @Override
    public List<TestSuiteExecutionDTO> testSuiteExecutionToDTOs(List<TestSuiteExecution> save) {
        if ( save == null ) {
            return null;
        }

        List<TestSuiteExecutionDTO> list = new ArrayList<TestSuiteExecutionDTO>( save.size() );
        for ( TestSuiteExecution testSuiteExecution : save ) {
            list.add( toDTO( testSuiteExecution ) );
        }

        return list;
    }

    @Override
    public TestFunctionArgumentDTO toDTO(FunctionArgument functionArgument) {
        if ( functionArgument == null ) {
            return null;
        }

        TestFunctionArgumentDTO testFunctionArgumentDTO = new TestFunctionArgumentDTO();

        testFunctionArgumentDTO.setName( functionArgument.getName() );
        testFunctionArgumentDTO.setType( functionArgument.getType() );
        testFunctionArgumentDTO.setOptional( functionArgument.isOptional() );
        testFunctionArgumentDTO.setDefaultValue( functionArgument.getDefaultValue() );
        testFunctionArgumentDTO.setArgOrder( functionArgument.getArgOrder() );

        return testFunctionArgumentDTO;
    }

    @Override
    public FunctionArgument fromDTO(TestFunctionArgumentDTO testFunctionArgument) {
        if ( testFunctionArgument == null ) {
            return null;
        }

        FunctionArgument.FunctionArgumentBuilder functionArgument = FunctionArgument.builder();

        functionArgument.name( testFunctionArgument.getName() );
        functionArgument.type( testFunctionArgument.getType() );
        functionArgument.optional( testFunctionArgument.isOptional() );
        functionArgument.defaultValue( testFunctionArgument.getDefaultValue() );
        functionArgument.argOrder( testFunctionArgument.getArgOrder() );

        return functionArgument.build();
    }

    @Override
    public TestFunctionDTO toDTO(TestFunction testFunction) {
        if ( testFunction == null ) {
            return null;
        }

        TestFunctionDTO testFunctionDTO = new TestFunctionDTO();

        testFunctionDTO.setUuid( testFunction.getUuid() );
        testFunctionDTO.setName( testFunction.getName() );
        testFunctionDTO.setDisplayName( testFunction.getDisplayName() );
        testFunctionDTO.setVersion( testFunction.getVersion() );
        testFunctionDTO.setModule( testFunction.getModule() );
        testFunctionDTO.setDoc( testFunction.getDoc() );
        testFunctionDTO.setModuleDoc( testFunction.getModuleDoc() );
        testFunctionDTO.setCode( testFunction.getCode() );
        List<String> list = testFunction.getTags();
        if ( list != null ) {
            testFunctionDTO.setTags( new ArrayList<String>( list ) );
        }
        testFunctionDTO.setArgs( functionArgumentListToTestFunctionArgumentDTOList( testFunction.getArgs() ) );

        return testFunctionDTO;
    }

    @Override
    public TestFunction fromDTO(TestFunctionDTO testFunction) {
        if ( testFunction == null ) {
            return null;
        }

        TestFunction testFunction1 = new TestFunction();

        testFunction1.setUuid( testFunction.getUuid() );
        testFunction1.setName( testFunction.getName() );
        testFunction1.setDisplayName( testFunction.getDisplayName() );
        if ( testFunction.getVersion() != null ) {
            testFunction1.setVersion( testFunction.getVersion() );
        }
        testFunction1.setModule( testFunction.getModule() );
        testFunction1.setDoc( testFunction.getDoc() );
        testFunction1.setModuleDoc( testFunction.getModuleDoc() );
        testFunction1.setCode( testFunction.getCode() );
        List<String> list = testFunction.getTags();
        if ( list != null ) {
            testFunction1.setTags( new ArrayList<String>( list ) );
        }
        testFunction1.setArgs( testFunctionArgumentDTOListToFunctionArgumentList( testFunction.getArgs() ) );

        return testFunction1;
    }

    @Override
    public SlicingFunction fromDTO(SlicingFunctionDTO testFunction) {
        if ( testFunction == null ) {
            return null;
        }

        SlicingFunction slicingFunction = new SlicingFunction();

        slicingFunction.setUuid( testFunction.getUuid() );
        slicingFunction.setName( testFunction.getName() );
        slicingFunction.setDisplayName( testFunction.getDisplayName() );
        if ( testFunction.getVersion() != null ) {
            slicingFunction.setVersion( testFunction.getVersion() );
        }
        slicingFunction.setModule( testFunction.getModule() );
        slicingFunction.setDoc( testFunction.getDoc() );
        slicingFunction.setModuleDoc( testFunction.getModuleDoc() );
        slicingFunction.setCode( testFunction.getCode() );
        List<String> list = testFunction.getTags();
        if ( list != null ) {
            slicingFunction.setTags( new ArrayList<String>( list ) );
        }
        slicingFunction.setArgs( testFunctionArgumentDTOListToFunctionArgumentList( testFunction.getArgs() ) );
        slicingFunction.setProjectKey( testFunction.getProjectKey() );
        slicingFunction.setCellLevel( testFunction.isCellLevel() );
        slicingFunction.setColumnType( testFunction.getColumnType() );
        slicingFunction.setProcessType( testFunction.getProcessType() );
        List<Map<String, Object>> list2 = testFunction.getClauses();
        if ( list2 != null ) {
            slicingFunction.setClauses( new ArrayList<Map<String, Object>>( list2 ) );
        }

        return slicingFunction;
    }

    @Override
    public SlicingFunctionDTO toDTO(SlicingFunction testFunction) {
        if ( testFunction == null ) {
            return null;
        }

        SlicingFunctionDTO slicingFunctionDTO = new SlicingFunctionDTO();

        slicingFunctionDTO.setUuid( testFunction.getUuid() );
        slicingFunctionDTO.setName( testFunction.getName() );
        slicingFunctionDTO.setDisplayName( testFunction.getDisplayName() );
        slicingFunctionDTO.setVersion( testFunction.getVersion() );
        slicingFunctionDTO.setModule( testFunction.getModule() );
        slicingFunctionDTO.setDoc( testFunction.getDoc() );
        slicingFunctionDTO.setModuleDoc( testFunction.getModuleDoc() );
        slicingFunctionDTO.setCode( testFunction.getCode() );
        List<String> list = testFunction.getTags();
        if ( list != null ) {
            slicingFunctionDTO.setTags( new ArrayList<String>( list ) );
        }
        slicingFunctionDTO.setArgs( functionArgumentListToTestFunctionArgumentDTOList( testFunction.getArgs() ) );
        slicingFunctionDTO.setCellLevel( testFunction.isCellLevel() );
        slicingFunctionDTO.setColumnType( testFunction.getColumnType() );
        slicingFunctionDTO.setProcessType( testFunction.getProcessType() );
        List<Map<String, Object>> list2 = testFunction.getClauses();
        if ( list2 != null ) {
            slicingFunctionDTO.setClauses( new ArrayList<Map<String, Object>>( list2 ) );
        }
        slicingFunctionDTO.setProjectKey( testFunction.getProjectKey() );

        return slicingFunctionDTO;
    }

    @Override
    public TransformationFunctionDTO toDTO(TransformationFunction testFunction) {
        if ( testFunction == null ) {
            return null;
        }

        TransformationFunctionDTO transformationFunctionDTO = new TransformationFunctionDTO();

        transformationFunctionDTO.setUuid( testFunction.getUuid() );
        transformationFunctionDTO.setName( testFunction.getName() );
        transformationFunctionDTO.setDisplayName( testFunction.getDisplayName() );
        transformationFunctionDTO.setVersion( testFunction.getVersion() );
        transformationFunctionDTO.setModule( testFunction.getModule() );
        transformationFunctionDTO.setDoc( testFunction.getDoc() );
        transformationFunctionDTO.setModuleDoc( testFunction.getModuleDoc() );
        transformationFunctionDTO.setCode( testFunction.getCode() );
        List<String> list = testFunction.getTags();
        if ( list != null ) {
            transformationFunctionDTO.setTags( new ArrayList<String>( list ) );
        }
        transformationFunctionDTO.setArgs( functionArgumentListToTestFunctionArgumentDTOList( testFunction.getArgs() ) );
        transformationFunctionDTO.setCellLevel( testFunction.isCellLevel() );
        transformationFunctionDTO.setColumnType( testFunction.getColumnType() );
        transformationFunctionDTO.setProcessType( testFunction.getProcessType() );
        List<Map<String, Object>> list2 = testFunction.getClauses();
        if ( list2 != null ) {
            transformationFunctionDTO.setClauses( new ArrayList<Map<String, Object>>( list2 ) );
        }
        transformationFunctionDTO.setProjectKey( testFunction.getProjectKey() );

        return transformationFunctionDTO;
    }

    @Override
    public TransformationFunction fromDTO(TransformationFunctionDTO testFunction) {
        if ( testFunction == null ) {
            return null;
        }

        TransformationFunction transformationFunction = new TransformationFunction();

        transformationFunction.setUuid( testFunction.getUuid() );
        transformationFunction.setName( testFunction.getName() );
        transformationFunction.setDisplayName( testFunction.getDisplayName() );
        if ( testFunction.getVersion() != null ) {
            transformationFunction.setVersion( testFunction.getVersion() );
        }
        transformationFunction.setModule( testFunction.getModule() );
        transformationFunction.setDoc( testFunction.getDoc() );
        transformationFunction.setModuleDoc( testFunction.getModuleDoc() );
        transformationFunction.setCode( testFunction.getCode() );
        List<String> list = testFunction.getTags();
        if ( list != null ) {
            transformationFunction.setTags( new ArrayList<String>( list ) );
        }
        transformationFunction.setArgs( testFunctionArgumentDTOListToFunctionArgumentList( testFunction.getArgs() ) );
        transformationFunction.setProjectKey( testFunction.getProjectKey() );
        transformationFunction.setCellLevel( testFunction.isCellLevel() );
        transformationFunction.setColumnType( testFunction.getColumnType() );
        transformationFunction.setProcessType( testFunction.getProcessType() );
        List<Map<String, Object>> list2 = testFunction.getClauses();
        if ( list2 != null ) {
            transformationFunction.setClauses( new ArrayList<Map<String, Object>>( list2 ) );
        }

        return transformationFunction;
    }

    protected List<UserDTO> userSetToUserDTOList(Set<User> set) {
        if ( set == null ) {
            return null;
        }

        List<UserDTO> list = new ArrayList<UserDTO>( set.size() );
        for ( User user : set ) {
            list.add( userToUserDTO( user ) );
        }

        return list;
    }

    private Long objProjectId(Feedback feedback) {
        if ( feedback == null ) {
            return null;
        }
        Project project = feedback.getProject();
        if ( project == null ) {
            return null;
        }
        Long id = project.getId();
        if ( id == null ) {
            return null;
        }
        return id;
    }

    protected List<FunctionInput> functionInputDTOListToFunctionInputList(List<FunctionInputDTO> list) {
        if ( list == null ) {
            return null;
        }

        List<FunctionInput> list1 = new ArrayList<FunctionInput>( list.size() );
        for ( FunctionInputDTO functionInputDTO : list ) {
            list1.add( fromDTO( functionInputDTO ) );
        }

        return list1;
    }

    protected List<SuiteTest> suiteTestDTOListToSuiteTestList(List<SuiteTestDTO> list) {
        if ( list == null ) {
            return null;
        }

        List<SuiteTest> list1 = new ArrayList<SuiteTest>( list.size() );
        for ( SuiteTestDTO suiteTestDTO : list ) {
            list1.add( fromDTO( suiteTestDTO ) );
        }

        return list1;
    }

    protected List<FunctionInputDTO> functionInputListToFunctionInputDTOList(List<FunctionInput> list) {
        if ( list == null ) {
            return null;
        }

        List<FunctionInputDTO> list1 = new ArrayList<FunctionInputDTO>( list.size() );
        for ( FunctionInput functionInput : list ) {
            list1.add( toDTO( functionInput ) );
        }

        return list1;
    }

    private String suiteProjectKey(TestSuite testSuite) {
        if ( testSuite == null ) {
            return null;
        }
        Project project = testSuite.getProject();
        if ( project == null ) {
            return null;
        }
        String key = project.getKey();
        if ( key == null ) {
            return null;
        }
        return key;
    }

    protected List<SuiteTestDTO> suiteTestListToSuiteTestDTOList(List<SuiteTest> list) {
        if ( list == null ) {
            return null;
        }

        List<SuiteTestDTO> list1 = new ArrayList<SuiteTestDTO>( list.size() );
        for ( SuiteTest suiteTest : list ) {
            list1.add( toDTO( suiteTest ) );
        }

        return list1;
    }

    private UUID dtoTestFunctionUuid(SuiteTest suiteTest) {
        if ( suiteTest == null ) {
            return null;
        }
        TestFunction testFunction = suiteTest.getTestFunction();
        if ( testFunction == null ) {
            return null;
        }
        UUID uuid = testFunction.getUuid();
        if ( uuid == null ) {
            return null;
        }
        return uuid;
    }

    private Long saveSuiteId(TestSuiteExecution testSuiteExecution) {
        if ( testSuiteExecution == null ) {
            return null;
        }
        TestSuite suite = testSuiteExecution.getSuite();
        if ( suite == null ) {
            return null;
        }
        Long id = suite.getId();
        if ( id == null ) {
            return null;
        }
        return id;
    }

    protected SuiteTestExecutionDTO suiteTestExecutionToSuiteTestExecutionDTO(SuiteTestExecution suiteTestExecution) {
        if ( suiteTestExecution == null ) {
            return null;
        }

        SuiteTestExecutionDTO suiteTestExecutionDTO = new SuiteTestExecutionDTO();

        suiteTestExecutionDTO.setTest( toDTO( suiteTestExecution.getTest() ) );
        Map<String, String> map = suiteTestExecution.getInputs();
        if ( map != null ) {
            suiteTestExecutionDTO.setInputs( new LinkedHashMap<String, String>( map ) );
        }
        Map<String, String> map1 = suiteTestExecution.getArguments();
        if ( map1 != null ) {
            suiteTestExecutionDTO.setArguments( new LinkedHashMap<String, String>( map1 ) );
        }
        List<TestResultMessageDTO> list = suiteTestExecution.getMessages();
        if ( list != null ) {
            suiteTestExecutionDTO.setMessages( new ArrayList<TestResultMessageDTO>( list ) );
        }
        List<Integer> list1 = suiteTestExecution.getActualSlicesSize();
        if ( list1 != null ) {
            suiteTestExecutionDTO.setActualSlicesSize( new ArrayList<Integer>( list1 ) );
        }
        List<Integer> list2 = suiteTestExecution.getReferenceSlicesSize();
        if ( list2 != null ) {
            suiteTestExecutionDTO.setReferenceSlicesSize( new ArrayList<Integer>( list2 ) );
        }
        suiteTestExecutionDTO.setStatus( suiteTestExecution.getStatus() );
        List<Integer> list3 = suiteTestExecution.getPartialUnexpectedIndexList();
        if ( list3 != null ) {
            suiteTestExecutionDTO.setPartialUnexpectedIndexList( new ArrayList<Integer>( list3 ) );
        }
        List<Integer> list4 = suiteTestExecution.getUnexpectedIndexList();
        if ( list4 != null ) {
            suiteTestExecutionDTO.setUnexpectedIndexList( new ArrayList<Integer>( list4 ) );
        }
        suiteTestExecutionDTO.setMissingCount( suiteTestExecution.getMissingCount() );
        suiteTestExecutionDTO.setMissingPercent( suiteTestExecution.getMissingPercent() );
        suiteTestExecutionDTO.setUnexpectedCount( suiteTestExecution.getUnexpectedCount() );
        suiteTestExecutionDTO.setUnexpectedPercent( suiteTestExecution.getUnexpectedPercent() );
        suiteTestExecutionDTO.setUnexpectedPercentTotal( suiteTestExecution.getUnexpectedPercentTotal() );
        suiteTestExecutionDTO.setUnexpectedPercentNonmissing( suiteTestExecution.getUnexpectedPercentNonmissing() );
        suiteTestExecutionDTO.setMetric( suiteTestExecution.getMetric() );

        return suiteTestExecutionDTO;
    }

    protected List<SuiteTestExecutionDTO> suiteTestExecutionListToSuiteTestExecutionDTOList(List<SuiteTestExecution> list) {
        if ( list == null ) {
            return null;
        }

        List<SuiteTestExecutionDTO> list1 = new ArrayList<SuiteTestExecutionDTO>( list.size() );
        for ( SuiteTestExecution suiteTestExecution : list ) {
            list1.add( suiteTestExecutionToSuiteTestExecutionDTO( suiteTestExecution ) );
        }

        return list1;
    }

    protected List<TestFunctionArgumentDTO> functionArgumentListToTestFunctionArgumentDTOList(List<FunctionArgument> list) {
        if ( list == null ) {
            return null;
        }

        List<TestFunctionArgumentDTO> list1 = new ArrayList<TestFunctionArgumentDTO>( list.size() );
        for ( FunctionArgument functionArgument : list ) {
            list1.add( toDTO( functionArgument ) );
        }

        return list1;
    }

    protected List<FunctionArgument> testFunctionArgumentDTOListToFunctionArgumentList(List<TestFunctionArgumentDTO> list) {
        if ( list == null ) {
            return null;
        }

        List<FunctionArgument> list1 = new ArrayList<FunctionArgument>( list.size() );
        for ( TestFunctionArgumentDTO testFunctionArgumentDTO : list ) {
            list1.add( fromDTO( testFunctionArgumentDTO ) );
        }

        return list1;
    }
}
