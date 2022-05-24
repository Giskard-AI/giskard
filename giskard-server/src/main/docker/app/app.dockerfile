FROM openjdk:17-buster as build
WORKDIR /workspace

COPY gradle gradle
COPY gradlew .
COPY gradle.properties .
COPY settings.gradle .

COPY giskard-common giskard-common

WORKDIR /workspace/giskard-server
COPY giskard-server/gradle gradle
COPY giskard-server/src src
COPY giskard-server/build.gradle .
COPY giskard-server/sonar-project.properties .

ARG RUN_TESTS=false
RUN bash -c "if [ "$RUN_TESTS" = true ] ; then  ../gradlew -Pprod clean test bootJar ; else ../gradlew -Pprod clean bootJar ; fi"

FROM openjdk:17-buster
COPY --from=build /workspace/giskard-server/build/libs/giskard*.jar /giskard/lib/giskard.jar
ENTRYPOINT ["java","-jar","/giskard/lib/giskard.jar"]
