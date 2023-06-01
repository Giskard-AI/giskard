export function groupBy<T>(keySelector: (data: T) => string):
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
