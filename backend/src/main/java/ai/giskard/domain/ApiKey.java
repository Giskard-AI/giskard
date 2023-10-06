package ai.giskard.domain;

import ai.giskard.security.GalleryDatabaseOperationListener;
import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.apache.commons.lang3.RandomStringUtils;

import java.util.UUID;

@Entity(name = "api_keys")
@Getter
@Setter
@NoArgsConstructor
@EntityListeners(GalleryDatabaseOperationListener.class)
public class ApiKey extends AbstractAuditingEntity {

    public static final String PREFIX = "gsk-";
    public static final int KEY_LENGTH = 32;
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @ManyToOne
    private User user;

    @Column(name = "api_key", length = KEY_LENGTH, unique = true, nullable = false)
    private String key;

    private String name;

    public ApiKey(User user) {
        this.user = user;
        id = UUID.randomUUID();
        key = PREFIX + RandomStringUtils.randomAlphanumeric(KEY_LENGTH - PREFIX.length()); //NOSONAR
    }

    public static boolean doesStringLookLikeApiKey(String str) {
        return str != null && str.length() == KEY_LENGTH && str.startsWith(PREFIX);
    }
}
