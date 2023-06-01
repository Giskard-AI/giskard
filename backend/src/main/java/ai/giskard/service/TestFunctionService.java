package ai.giskard.service;

import ai.giskard.domain.TestFunction;
import ai.giskard.domain.TestFunctionArgument;
import ai.giskard.ml.MLWorkerClient;
import ai.giskard.repository.ProjectRepository;
import ai.giskard.repository.ml.TestFunctionRepository;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.TestFunctionArgumentDTO;
import ai.giskard.web.dto.TestFunctionDTO;
import ai.giskard.web.dto.mapper.GiskardMapper;
import ai.giskard.worker.MLWorkerGrpc;
import ai.giskard.worker.TestRegistryResponse;
import com.google.protobuf.Empty;
import io.grpc.StatusRuntimeException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import javax.transaction.Transactional;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static ai.giskard.utils.GRPCUtils.convertGRPCObject;

@Service
@RequiredArgsConstructor
public class TestFunctionService {

    private final GiskardMapper giskardMapper;
    private final TestFunctionRepository testFunctionRepository;
    private final ProjectRepository projectRepository;
    private final MLWorkerService mlWorkerService;

    @Transactional
    public TestFunctionDTO save(TestFunctionDTO testFunction) {
        return giskardMapper.toDTO(testFunctionRepository.save(testFunctionRepository.findById(testFunction.getUuid())
            .map(existing -> update(existing, testFunction))
            .orElseGet(() -> create(testFunction))));
    }

    private TestFunction create(TestFunctionDTO dto) {
        TestFunction function = giskardMapper.fromDTO(dto);
        function.getArgs().forEach(arg -> arg.setTestFunction(function));
        function.setVersion(testFunctionRepository.countByNameAndModule(function.getName(), function.getModule()) + 1);
        return function;
    }

    private TestFunction update(TestFunction existing, TestFunctionDTO dto) {
        existing.setDoc(dto.getDoc());
        existing.setModuleDoc(dto.getModuleDoc());
        existing.setCode(dto.getCode());
        existing.setTags(dto.getTags());

        Map<String, TestFunctionArgument> existingArgs = existing.getArgs().stream()
                .collect(Collectors.toMap(TestFunctionArgument::getName, Function.identity()));
        Map<String, TestFunctionArgumentDTO> currentArgs = dto.getArgs().stream()
            .collect(Collectors.toMap(TestFunctionArgumentDTO::getName, Function.identity()));

        // Delete removed args
        existingArgs.entrySet().stream()
            .filter(entry -> !currentArgs.containsKey(entry.getKey()))
            .forEach(entry -> existing.getArgs().remove(entry.getValue()));

        // Update or create current args
        currentArgs.forEach((name, currentArg) -> {
            if (existingArgs.containsKey(name)) {
                TestFunctionArgument existingArg = existingArgs.get(name);
                existingArg.setType(currentArg.getType());
                existingArg.setOptional(currentArg.isOptional());
                existingArg.setDefaultValue(currentArg.getDefaultValue());
            } else {
                existing.getArgs().add(giskardMapper.fromDTO(currentArg));
            }
        });

        return existing;
    }

    @Transactional
    public List<TestFunctionDTO> findAll(long projectId) {
        return Stream.concat(testFunctionRepository.findAll().stream().map(giskardMapper::toDTO),
                findGiskardTest(projectRepository.getById(projectId).isUsingInternalWorker()).stream())
            .toList();
    }

    private List<TestFunctionDTO> findGiskardTest(boolean isInternal) {
        try (MLWorkerClient client = mlWorkerService.createClientNoError(isInternal)) {
            if (!isInternal && client == null) {
                // Fallback to internal ML worker to not display empty catalog
                return findGiskardTest(true).stream()
                    .map(dto -> dto.toBuilder().potentiallyUnavailable(true).build())
                    .toList();
            } else if (client == null) {
                return Collections.emptyList();
            }

            MLWorkerGrpc.MLWorkerBlockingStub blockingStub = client.getBlockingStub();
            TestRegistryResponse response = blockingStub.getTestRegistry(Empty.newBuilder().build());
            return response.getTestsMap().values().stream()
                .map(test -> convertGRPCObject(test, TestFunctionDTO.class))
                .toList();
        } catch (StatusRuntimeException e) {
            return Collections.emptyList();
        }
    }

}
