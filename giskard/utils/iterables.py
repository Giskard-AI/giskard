import itertools


def batched(iterable, batch_size):
    """Batches an iterable into chunks of size batch_size."""
    it = iter(iterable)
    while True:
        chunk = list(itertools.islice(it, batch_size))
        if not chunk:
            break
        yield chunk
