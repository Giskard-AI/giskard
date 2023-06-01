export function plurialize(text: string, count: number): string {
    return `${count} ${text}${count > 1 ? 's' : ''}`
}
