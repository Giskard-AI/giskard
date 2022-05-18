package ai.giskard.web.dto;

import com.dataiku.j2ts.annotations.UIModel;
import lombok.AllArgsConstructor;
import lombok.Getter;
import org.slf4j.helpers.MessageFormatter;

import java.text.MessageFormat;

@UIModel
@Getter
public class MessageDTO {
    private String message;

    public MessageDTO(String message, Object... args) {
        this.message = MessageFormatter.arrayFormat(message, args).getMessage();
    }
}
