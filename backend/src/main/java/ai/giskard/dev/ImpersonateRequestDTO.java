package ai.giskard.dev;

import lombok.Getter;
import lombok.Setter;

@Getter
@Setter
class ImpersonateRequestDTO {
    private String sc;
    private String login;
    private Long id;
    private String authorities;
}
