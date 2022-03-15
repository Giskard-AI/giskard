FROM openjdk:17-buster as build
WORKDIR /workspace/giskard

COPY gradle gradle
COPY build.gradle .
COPY gradlew .
COPY gradle.properties .
COPY sonar-project.properties .
COPY src src

RUN ./gradlew -Pprod clean bootJar

FROM openjdk:17-buster
COPY --from=build /workspace/giskard/build/libs/giskard*.jar /giskard/lib/giskard.jar
ENTRYPOINT ["java","-jar","/giskard/lib/giskard.jar"]
