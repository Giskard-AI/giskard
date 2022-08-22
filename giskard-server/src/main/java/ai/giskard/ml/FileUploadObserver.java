package ai.giskard.ml;

import ai.giskard.worker.UploadStatus;
import io.grpc.stub.StreamObserver;

class FileUploadObserver implements StreamObserver<UploadStatus> {

    @Override
    public void onNext(UploadStatus uploadStatus) {
        System.out.println("FileUploadObserver: File upload status :: " + uploadStatus.getCode());
    }

    @Override
    public void onError(Throwable throwable) {
        System.out.println("FileUploadObserver: onError");
    }

    @Override
    public void onCompleted() {
        System.out.println("FileUploadObserver: onCompleted");
    }

}
