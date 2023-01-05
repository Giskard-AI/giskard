package ai.giskard.service.ee.licensing;

import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;

@Service
public class KeygenLicenseService implements IExternalLicenseProvider {

    private final WebClient client;

    public KeygenLicenseService() {
        client = WebClient.builder()
            .baseUrl("https://api.keygen.sh/v1/accounts/d6f37322-26a6-4fe7-8770-50a781666581")
            .defaultHeader(HttpHeaders.CONTENT_TYPE, "application/vnd.api+json")
            .defaultHeader(HttpHeaders.ACCEPT, "application/vnd.api+json")
            .build();
    }

    private boolean validateLicense() {
        String licenseResult = client
            .post()
            .uri("/licenses/actions/validate-key")
            .bodyValue("""
                {
                    "meta": {
                        "key": "750FE7-0EDB4A-ECFF20-F88782-154561-V3"
                    }
                }
                """)
            .retrieve()
            .bodyToMono(String.class)
            .block();

        return true;
    }

    private void getEntitlements() {
    }

    @Override
    public License getLicense() {
        return null;
    }
}
