FROM openjdk:17-buster as build
WORKDIR /workspace/giskard

COPY ./java-app/gradle gradle
COPY ./java-app/build.gradle .
COPY ./java-app/gradlew .
COPY ./java-app/gradle.properties .
COPY ./java-app/sonar-project.properties .
COPY ./java-app/src src

RUN rm -rf src/main/proto
COPY ./java-app/src/main/proto src/main/proto

RUN ./gradlew -Pprod clean bootJar

FROM openjdk:17-buster
COPY --from=build /workspace/giskard/build/libs/giskard*.jar /giskard/lib/giskard.jar
ENTRYPOINT ["java","-jar","/giskard/lib/giskard.jar"]
