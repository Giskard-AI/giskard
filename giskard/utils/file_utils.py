def get_file_name(name: str, extension: str, sample: bool):
    return f"{name}.sample.{extension}" if sample else f"{name}.{extension}"
