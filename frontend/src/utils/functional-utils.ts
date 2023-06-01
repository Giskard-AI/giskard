/**
 * Only execute the function when the equals method return false based on previous arguments
 * @param func
 * @param equals
 */
export function computeOnValueChanged<T, R>(func: (value: T) => R, equals: (l: T, r: T) => boolean): (value: T) => R {
    let cache: {
        lastVal: T | null,
        lastRes: R | null
    } = {
        lastVal: null,
        lastRes: null
    };

    return (value) => {
        if (cache.lastVal === null || !equals(value, cache.lastVal)) {
            cache.lastVal = value;
            cache.lastRes = func(value);
        }

        return cache.lastRes as R;
    };
}

export const voidFunction = () => {};
