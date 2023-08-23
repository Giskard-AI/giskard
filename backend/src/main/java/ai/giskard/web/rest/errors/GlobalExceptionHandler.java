package ai.giskard.web.rest.errors;

import org.jetbrains.annotations.NotNull;
import org.springframework.dao.ConcurrencyFailureException;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.NativeWebRequest;
import org.springframework.web.servlet.mvc.method.annotation.ResponseEntityExceptionHandler;

@RestControllerAdvice
public class GlobalExceptionHandler extends ResponseEntityExceptionHandler {

    @ExceptionHandler
    public ResponseEntity<Object> handleAnyException(Throwable ex, NativeWebRequest request) {
        return handleExceptionInternal(
            (Exception) ex,
            ProblemDetail.forStatusAndDetail(
                getHttpStatus(ex),
                ex.getMessage()
            ),
            null,
            getHttpStatus(ex),
            request
        );
    }

    @NotNull
    private static HttpStatus getHttpStatus(Throwable ex) {
        if (ex instanceof ConcurrencyFailureException) return HttpStatus.CONFLICT;
        if (ex instanceof BadCredentialsException) return HttpStatus.UNAUTHORIZED;
        if (ex instanceof AccessDeniedException) return HttpStatus.FORBIDDEN;
        return HttpStatus.INTERNAL_SERVER_ERROR;
    }
}
