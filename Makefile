generate-python:
	# pip install grpcio grpcio-tools mypy-protobuf types-protobuf
	python3.7 -m grpc_tools.protoc -Ibackend/java-app/src/main/proto --python_out=backend/java-app/src/main/python/generated --grpc_python_out=backend/java-app/src/main/python/generated --mypy_out=backend/java-app/src/main/python/generated backend/java-app/src/main/proto/ml-worker.proto