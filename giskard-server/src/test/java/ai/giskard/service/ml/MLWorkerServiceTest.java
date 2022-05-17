package ai.giskard.service.ml;

import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.worker.RunModelResponse;
import com.google.common.util.concurrent.ListenableFuture;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.transaction.annotation.Transactional;

import java.io.IOException;
import java.nio.file.Files;
import java.util.concurrent.ExecutionException;

@AutoConfigureMockMvc
@ExtendWith(SpringExtension.class)
@SpringBootTest
@Transactional
class MLWorkerServiceTest {
    @Autowired
    private MLWorkerService mlWorkerService;
    @Autowired
    private ProjectRepository projectRepository;

    @Test
    public void testRunModel() throws InterruptedException, ExecutionException, IOException {
        //MLWorkerClient client = mlWorkerService.createClient();
        //ListenableFuture<RunModelResponse> result = client.runModel(Files.newInputStream(modelPath), Files.newInputStream(datasetPath));
        //RunModelResponse runModelResponse = result.get();
        //System.out.println(1);
    }
}
