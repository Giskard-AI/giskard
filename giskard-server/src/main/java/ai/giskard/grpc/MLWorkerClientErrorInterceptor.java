package ai.giskard.grpc;

import ai.giskard.exception.MLWorkerRuntimeException;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.rpc.DebugInfo;
import io.grpc.*;
import io.grpc.protobuf.StatusProto;
import org.apache.commons.lang3.exception.ExceptionUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MLWorkerClientErrorInterceptor implements ClientInterceptor {
    private final Logger log = LoggerFactory.getLogger(MLWorkerClientErrorInterceptor.class);

    @Override
    public <Q, P> ClientCall<Q, P> interceptCall(MethodDescriptor<Q, P> method, CallOptions callOptions, Channel channel) {
        return new ForwardingClientCall.SimpleForwardingClientCall<>(channel.newCall(method, callOptions)) {
            @Override
            public void start(Listener<P> responseListener, Metadata headers) {
                super.start(new ForwardingClientCallListener.SimpleForwardingClientCallListener<>(responseListener) {
                    @Override
                    public void onClose(Status basicStatus, Metadata trailers) {
                        if (basicStatus.isOk()) {
                            super.onClose(basicStatus, trailers);
                        } else {
                            com.google.rpc.Status status = StatusProto.fromStatusAndTrailers(basicStatus, trailers);
                            DebugInfo debugInfo = extractDebugInfo(status);

                            MLWorkerRuntimeException cause = new MLWorkerRuntimeException(
                                basicStatus,
                                status.getMessage(),
                                debugInfo == null ? null : debugInfo.getDetail(),
                                debugInfo == null ? null : debugInfo.getStackEntriesList().stream().toList());

                            basicStatus = interpretErrorStatus(basicStatus);
                            super.onClose(basicStatus.withCause(cause), trailers);
                        }
                    }
                }, headers);
            }
        };
    }

    private Status interpretErrorStatus(Status basicStatus) {
        if (basicStatus.getCode() == Status.Code.UNAVAILABLE) {
            basicStatus = basicStatus.withDescription("Failed to connect to ML Worker, check that it's running");
        }
        return basicStatus;
    }

    private DebugInfo extractDebugInfo(com.google.rpc.Status status) {
        DebugInfo debugInfo = null;
        if (status.getDetailsCount() > 0 && status.getDetails(0).is(DebugInfo.class)) {
            try {
                debugInfo = status.getDetails(0).unpack(DebugInfo.class);
            } catch (InvalidProtocolBufferException ex) {
                log.warn("Failed to extract debugInfo from exception {}", ExceptionUtils.getMessage(ex));
            }
        }
        return debugInfo;
    }

}
