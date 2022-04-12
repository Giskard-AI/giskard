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


RUN ../gradlew -Pprod clean bootJar

FROM openjdk:17-buster
COPY --from=build /workspace/giskard-server/build/libs/giskard*.jar /giskard/lib/giskard.jar
COPY giskard-server/src/main/docker/app/wait-for-python-app.sh /giskard/
#ENTRYPOINT ["java","-jar","/giskard/lib/giskard.jar"]
