.PHONY: all test clean backend


generate-java:
	./backend/java-app/gradlew -b backend/java-app/build.gradle clean generateProto	


backend:
	cd ./backend/java-app && ./gradlew build -x test -x integrationTest


liquibase-difflog:
	cd ./backend/java-app && ./gradlew liquibaseDiffChangelog -PrunList=diffLog
