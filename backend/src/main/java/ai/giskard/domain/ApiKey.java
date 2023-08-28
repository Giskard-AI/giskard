package ai.giskard.domain;

import jakarta.persistence.*;
import jakarta.validation.constraints.Size;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.apache.commons.lang3.RandomStringUtils;
import org.hibernate.validator.constraints.Length;

import java.util.UUID;

@Entity(name = "api_keys")
@Getter
@NoArgsConstructor
public class ApiKey extends AbstractAuditingEntity {

    public static final String PREFIX = "gsk-";
    public static final int KEY_LENGTH = 32;
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    private User user;

    @Size(max = KEY_LENGTH, min = KEY_LENGTH)
    @Length(max = KEY_LENGTH, min = KEY_LENGTH)
    private String key;

    private String name;

    public ApiKey(User user) {
        this.user = user;
        id = UUID.randomUUID();
        key = PREFIX + RandomStringUtils.randomAlphanumeric(KEY_LENGTH - PREFIX.length());
    }

    public static boolean doesStringLookLikeApiKey(String str) {
        return str != null && str.length() == KEY_LENGTH && str.startsWith(PREFIX);
    }
}
