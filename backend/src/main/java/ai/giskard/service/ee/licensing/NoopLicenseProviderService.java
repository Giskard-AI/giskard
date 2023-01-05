package ai.giskard.service.ee.licensing;

import org.springframework.stereotype.Service;

@Service
public class NoopLicenseProviderService implements IExternalLicenseProvider {
    @Override
    public License getLicense() {
        return new License("", GiskardEdition.OPEN_SOURCE);
    }
}
