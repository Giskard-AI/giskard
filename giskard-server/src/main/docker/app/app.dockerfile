FROM eclipse-temurin:17 as build
WORKDIR /workspace

COPY gradle gradle
COPY giskard-common giskard-common
COPY sonar-project.properties .
COPY gradlew .
COPY gradle.properties .
COPY settings.gradle.kts .
COPY build.gradle.kts .
# Copying .git to make gradle-git-properties gradle plugin work
COPY .git .git

COPY giskard-server giskard-server

ARG RUN_TESTS=false

WORKDIR /workspace/giskard-server
RUN bash -c "if [ "$RUN_TESTS" = true ] ; then  ../gradlew -Pprod clean test bootJar --info --stacktrace; else ../gradlew -Pprod clean bootJar --info --stacktrace ; fi"

FROM eclipse-temurin:17-jre
COPY --from=build /workspace/giskard-server/build/libs/giskard*.jar /giskard/lib/giskard.jar
ENTRYPOINT ["java","-jar","/giskard/lib/giskard.jar"]
