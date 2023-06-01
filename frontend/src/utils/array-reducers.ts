export class ArrayReducers {
    static groupBy<T>(keySelector: (data: T) => string):
        (previousValue: { [key: string]: T[] }, currentValue: T) => { [key: string]: T[] } {
        return (data, result) => {
            const key = keySelector(result);

            if (data[key] !== undefined) {
                data[key].push(result);
            } else {
                data[key] = [result];
            }

            return data;
        }
    }

    static toMap<T, K extends string | number, U>(keySelector: (data: T) => K, valueSelector: (data: T) => U):
        (previousValue: { [key in K]: U }, currentValue: T) => { [key in K]: U } {
        return (data, result) => {
            data[keySelector(result)] = valueSelector(result);
            return data;
        }
    }
    
}
