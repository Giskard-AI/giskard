export class Comparators {

    static comparing<T, R>(selector: (obj: T) => R): (l: T, r: T) => number {
        return (l, r) => Comparators.compare(selector(l), selector(r));
    }

    static compare<T>(left: T, right: T): number {
        return left > right ? 1 : left < right ? -1 : 0;
    }

}
