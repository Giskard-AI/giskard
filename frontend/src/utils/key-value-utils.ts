import {ArrayReducers} from '@/utils/array-reducers';

type KeyValuePairs<T> = { [key: string]: T };

export class KeyValueUtils {

    static mapValues<T, U>(keyValues: KeyValuePairs<T>, mapper: (value: T) => U): KeyValuePairs<U> {
        return Object.entries(keyValues)
            .reduce(ArrayReducers.toMap<[string, T], string, U>(([key, _value]) => key, ([_key, value]) => mapper(value)), {});
    }
}
