generate-python:
	cd ./backend/ml-worker && ./generate-proto.sh

generate-java:
	./backend/java-app/gradlew -b backend/java-app/build.gradle clean generateProto	

generate-proto: generate-java generate-python

clean: clean-generated-java clean-generated-python

clean-generated-python:
	@rm -rf backend/ml-worker/generated

clean-generated-java:
	./backend/java-app/gradlew -b backend/java-app/build.gradle clean
