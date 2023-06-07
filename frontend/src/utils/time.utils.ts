const rtf = new Intl.RelativeTimeFormat('en');

const UNITS: Array<{ seconds: number, value: Intl.RelativeTimeFormatUnit }> = [{
    seconds: 31536000,
    value: 'year'
}, {
    seconds: 2592000,
    value: 'month'
}, {
    seconds: 86400,
    value: 'day'
}, {
    seconds: 3600,
    value: 'hour'
}, {
    seconds: 60,
    value: 'minute'
}, {
    seconds: 1,
    value: 'second'
}]

export function timeSince(date: Date) {
    const seconds = Math.floor((new Date().getTime() - new Date(date).getTime()) / 1000);

    for (const unit of UNITS) {
        const interval = seconds / unit.seconds;
        if (interval > 1) {
            return rtf.format(-Math.floor(interval), unit.value);
        }
    }

    return rtf.format(-1, 'second');

}
