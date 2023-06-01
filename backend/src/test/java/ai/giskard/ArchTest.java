package ai.giskard;

import com.tngtech.archunit.core.domain.JavaClasses;
import com.tngtech.archunit.core.importer.ClassFileImporter;
import com.tngtech.archunit.core.importer.ImportOption;
import org.junit.jupiter.api.Disabled;
import org.junit.jupiter.api.Test;

import static com.tngtech.archunit.lang.syntax.ArchRuleDefinition.noClasses;

@Disabled("Andrey: To be restored later")
class ArchTest {

    @Test
    void servicesAndRepositoriesShouldNotDependOnWebLayer() {
        JavaClasses importedClasses = new ClassFileImporter()
            .withImportOption(ImportOption.Predefined.DO_NOT_INCLUDE_TESTS)
            .importPackages("ai.giskard");

        noClasses()
            .that()
            .resideInAnyPackage("ai.giskard.service..")
            .or()
            .resideInAnyPackage("ai.giskard.repository..")
            .should()
            .dependOnClassesThat()
            .resideInAnyPackage("..ai.giskard.web..")
            .because("Services and repositories should not depend on web layer")
            .check(importedClasses);
    }
}
