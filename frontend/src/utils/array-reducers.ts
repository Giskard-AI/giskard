export class ArrayReducers {

    static toMap<T, K extends string | number, U>(keySelector: (data: T) => K, valueSelector: (data: T) => U):
        (previousValue: { [key in K]: U }, currentValue: T) => { [key in K]: U } {
        return (data, result) => {
            data[keySelector(result)] = valueSelector(result);
            return data;
        }
    }

}
