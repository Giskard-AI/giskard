mkdir -p generated
python3.7 -m grpc_tools.protoc \
  -Iml_worker/proto \
  --python_out=generated \
  --grpc_python_out=generated \
  --mypy_out=generated \
  ml_worker/proto/ml-worker.proto
