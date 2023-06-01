export function getColumnType(pythonType: string): string | null {
    switch (pythonType) {
        case 'str':
            return 'text';
        case 'int':
        case 'float':
            return 'numeric';
        default:
            return null;
    }
}
