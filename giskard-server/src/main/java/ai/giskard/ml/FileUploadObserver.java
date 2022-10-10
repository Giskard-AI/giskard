package ai.giskard.ml;

import ai.giskard.worker.UploadStatus;
import io.grpc.stub.StreamObserver;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

class FileUploadObserver implements StreamObserver<UploadStatus> {
    private final Logger log = LoggerFactory.getLogger(getClass());

    @Override
    public void onNext(UploadStatus uploadStatus) {
        log.debug("FileUploadObserver: File upload status :: " + uploadStatus.getCode());
    }

    @Override
    public void onError(Throwable throwable) {
        log.debug("FileUploadObserver: onError");
    }

    @Override
    public void onCompleted() {
        log.debug("FileUploadObserver: onCompleted");
    }

}
