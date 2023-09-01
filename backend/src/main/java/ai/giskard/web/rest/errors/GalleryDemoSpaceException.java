package ai.giskard.web.rest.errors;

import org.springframework.http.HttpStatus;

public class GalleryDemoSpaceException extends GiskardException {
    public GalleryDemoSpaceException(String description) {
        super(HttpStatus.SERVICE_UNAVAILABLE, description);
    }
}
