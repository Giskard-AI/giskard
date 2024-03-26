try:
    from tqdm.auto import tqdm, trange

    maybe_trange = trange
    maybe_tqdm = tqdm
except ImportError:

    def maybe_trange(*args, **kwargs):
        return range(*args, **kwargs)

    def maybe_tqdm(x, *args, **kwargs):
        return x
