mkdir -p generated
PYTHON="${1:-python3.7}"

$PYTHON -m grpc_tools.protoc \
  -Iml_worker/proto \
  --python_out=generated \
  --grpc_python_out=generated \
  --mypy_out=generated \
  ml_worker/proto/ml-worker.proto
