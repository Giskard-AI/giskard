FROM openjdk:17-buster
COPY ./build/libs/giskard*.jar /giskard/lib/giskard.jar
COPY ./src/main/docker/app/wait-for-python-app.sh /giskard/
# TODO Andrey: restore once python backend is removed and  wait-for-python-app.sh is not needed
#ENTRYPOINT ["java","-jar","/giskard/lib/giskard.jar"]
