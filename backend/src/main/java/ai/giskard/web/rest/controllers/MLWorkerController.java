package ai.giskard.web.rest.controllers;

import ai.giskard.ml.MLWorkerClient;
import ai.giskard.service.ml.MLWorkerService;
import ai.giskard.web.dto.config.MLWorkerInfoDTO;
import ai.giskard.worker.MLWorkerInfo;
import ai.giskard.worker.MLWorkerInfoRequest;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.google.common.util.concurrent.Futures;
import com.google.common.util.concurrent.ListenableFuture;
import com.google.protobuf.Empty;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.protobuf.util.JsonFormat;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v2/ml-workers")
public class MLWorkerController {

    private final MLWorkerService mlWorkerService;

    @GetMapping()
    public List<MLWorkerInfoDTO> getMLWorkerInfo() throws JsonProcessingException, InvalidProtocolBufferException, ExecutionException, InterruptedException {
        try (MLWorkerClient internalClient = mlWorkerService.createClientNoError(true);
             MLWorkerClient externalClient = mlWorkerService.createClientNoError(false)) {
            List<ListenableFuture<MLWorkerInfo>> awaitableResults = new ArrayList<>();

            if (internalClient != null) {
                awaitableResults.add(internalClient.getFutureStub().getInfo(MLWorkerInfoRequest.newBuilder().setListPackages(true).build()));
            }
            if (externalClient != null) {
                awaitableResults.add(externalClient.getFutureStub().getInfo(MLWorkerInfoRequest.newBuilder().setListPackages(true).build()));
            }

            List<MLWorkerInfo> mlWorkerInfos = Futures.successfulAsList(awaitableResults).get();
            List<MLWorkerInfoDTO> res = new ArrayList<>();
            for (MLWorkerInfo info : mlWorkerInfos) {
                if (info != null) {
                    res.add(new ObjectMapper().readValue(JsonFormat.printer().print(info), MLWorkerInfoDTO.class));
                }
            }

            return res;
        }
    }

    @PostMapping("/stop")
    public void stopWorker(boolean internal) {
        try (MLWorkerClient internalClient = mlWorkerService.createClientNoError(internal)) {
            internalClient.getBlockingStub().stopWorker(Empty.newBuilder().build());
        } catch (Exception ignored) {
            // TODO: check if there is a cleaner way to stop ML Worker without interrupting the current request
        }
    }

}
