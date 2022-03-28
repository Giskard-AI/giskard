generate-python:
	# pip install grpcio grpcio-tools mypy-protobuf types-protobuf
	@mkdir -p backend/java-app/build/generated/source/proto/main/python && \
	python3.7 -m grpc_tools.protoc \
		-Ibackend/java-app/src/main/proto \
		--python_out=backend/java-app/build/generated/source/proto/main/python \
		--grpc_python_out=backend/java-app/build/generated/source/proto/main/python \
		--mypy_out=backend/java-app/build/generated/source/proto/main/python \
		backend/java-app/src/main/proto/ml-worker.proto


generate-java:
	./backend/java-app/gradlew -b backend/java-app/build.gradle clean generateProto	

generate-proto: generate-java generate-python	