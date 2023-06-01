def is_in_ipython():
    return get_ipython() is not None  # noqa


def is_local_function(full_name: str):
    return full_name.startswith('__main__')
