package ai.giskard.service;

import ai.giskard.domain.ml.Dataset;
import ai.giskard.domain.ml.Inspection;
import ai.giskard.domain.ml.ProjectModel;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.InspectionRepository;
import ai.giskard.repository.ml.DatasetRepository;
import ai.giskard.repository.ml.ModelRepository;
import ai.giskard.security.PermissionEvaluator;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.worker.*;
import com.google.protobuf.ByteString;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

@Service
@Transactional
@RequiredArgsConstructor
public class ModelService {
    final DatasetRepository datasetRepository;
    final ModelRepository modelRepository;
    final PermissionEvaluator permissionEvaluator;
    final InspectionRepository inspectionRepository;
    private final MLWorkerService mlWorkerService;
    private final FileLocationService locationService;
    private final FileLocationService fileLocationService;

    public RunModelForDataFrameResponse predict(ProjectModel model, Map<String, String> features) {
        Path modelPath = locationService.resolvedModelPath(model.getProject().getKey(), model.getId());
        RunModelForDataFrameResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient()) {
            response = client.runModelForDataframe(
                Files.newInputStream(modelPath),
                DataFrame.newBuilder().addRows(DataRow.newBuilder().putAllFeatures(features)).build());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return response;
    }

    public ExplainResponse explain(ProjectModel model, Dataset dataset, Map<String, String> features) {
        Path datasetPath = locationService.resolvedDatasetPath(dataset.getProject().getKey(), dataset.getId());
        Path modelPath = locationService.resolvedModelPath(model.getProject().getKey(), model.getId());


        ExplainResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient()) {
            response = client.explain(
                Files.newInputStream(modelPath),
                Files.newInputStream(datasetPath),
                features);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return response;
    }


    public ExplainTextResponse explainText(ProjectModel model, String featureName, Map<String, String> features) {
        Path modelPath = locationService.resolvedModelPath(model.getProject().getKey(), model.getId());
        ExplainTextResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient()) {
            response = client.getBlockingStub().explainText(
                ExplainTextRequest.newBuilder()
                    .setSerializedModel(ByteString.readFrom(Files.newInputStream(modelPath)))
                    .setFeatureName(featureName)
                    .putAllFeatures(features)
                    .build()
            );
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return response;
    }


    public Inspection createInspection(Long modelId, Long datasetId) {
        ProjectModel model = modelRepository.getById(modelId);
        Dataset dataset = datasetRepository.getById(datasetId);
        permissionEvaluator.validateCanReadProject(model.getProject().getId());

        Inspection inspection = new Inspection();
        inspection.setDataset(dataset);
        inspection.setModel(model);
        inspection = inspectionRepository.save(inspection);

        RunModelResponse predictions = predictSerializedDataset(model, dataset);
        if (predictions == null) {
            return inspection;
        }
        Path inspectionPath = fileLocationService.resolvedInspectionPath(model.getProject().getKey(), inspection.getId());
        try {
            Files.createDirectories(inspectionPath);
            Files.write(inspectionPath.resolve("predictions.csv"), predictions.getResultsCsvBytes().toByteArray());
            Files.write(inspectionPath.resolve("calculated.csv"), predictions.getCalculatedCsvBytes().toByteArray());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
        return inspection;
    }

    private RunModelResponse predictSerializedDataset(ProjectModel model, Dataset dataset) {
        Path datasetPath = locationService.resolvedDatasetPath(dataset.getProject().getKey(), dataset.getId());
        Path modelPath = locationService.resolvedModelPath(model.getProject().getKey(), model.getId());


        RunModelResponse response;
        try (MLWorkerClient client = mlWorkerService.createClient()) {
            response = client.runModelForDataStream(Files.newInputStream(modelPath), Files.newInputStream(datasetPath), model.getTarget());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }

        return response;


        //PipedInputStream pipedInputStream = new PipedInputStream();
        //PipedOutputStream pipedOutputStream;

        //
        //try {
        //    pipedOutputStream = new PipedOutputStream(pipedInputStream);
        //    //new Thread(() -> {
        //    //    uploadService.d@ecompressFileToStream(path);
        //    //}).start();
        //
        //    //InputStream initialStream = new FileInputStream(
        //    //    new File("src/main/resources/sample.txt"));
        //    File targetFile = new File("/tmp/df.tmp");
        //
        //    //java.nio.file.Files.copy(
        //    //    uploadService.decompressFileToStream(path),
        //    //    targetFile.toPath(),
        //    //    StandardCopyOption.REPLACE_EXISTING);
        //
        //    IOUtils.closeQuietly(pipedInputStream);
        //
        //
        //    Table csv = Table.read().csv(new InputStreamReader(pipedInputStream));
        //
        //    System.out.println(1);
        //} catch(
        //IOException e)
        //
        //{
        //    throw new RuntimeException(e);
        //}

    }

}
