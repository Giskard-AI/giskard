dependencies {
    testImplementation("com.h2database:h2")
}

val profiles = "prod"
if (project.hasProperty("no-liquibase")) {
    profiles += ",no-liquibase"
}

if (project.hasProperty("api-docs")) {
    profiles += ",api-docs"
}

springBoot {
    buildInfo()
}

bootRun {
    args = listOf()
}


processResources {
    inputs.property("version", version)
    inputs.property("springProfiles", profiles)
    filesMatching("**/application.yml") {
        filter {
            it.replace("#project.version#", version)
        }
    }
}

