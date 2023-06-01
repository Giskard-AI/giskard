package ai.giskard.grpc;

import ai.giskard.exception.MLWorkerException;
import ai.giskard.worker.MLWorkerErrorInfo;
import com.google.protobuf.InvalidProtocolBufferException;
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
                            MLWorkerErrorInfo errorInfo = extractErrorInfo(status);

                            MLWorkerException cause = new MLWorkerException(
                                basicStatus,
                                status.getMessage(),
                                errorInfo == null ? null : errorInfo.getError(),
                                errorInfo == null ? null : errorInfo.getStack());

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
            basicStatus = basicStatus.withDescription("Failed to connect to ML Worker, check that it's running.");
        }
        return basicStatus;
    }

    private MLWorkerErrorInfo extractErrorInfo(com.google.rpc.Status status) {
        MLWorkerErrorInfo errorInfo = null;
        if (status.getDetailsCount() > 0 && status.getDetails(0).is(MLWorkerErrorInfo.class)) {
            try {
                errorInfo = status.getDetails(0).unpack(MLWorkerErrorInfo.class);
            } catch (InvalidProtocolBufferException ex) {
                log.warn("Failed to extract errorInfo from exception {}", ExceptionUtils.getMessage(ex));
            }
        }
        return errorInfo;
    }

}
