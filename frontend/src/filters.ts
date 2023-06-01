import Vue from "vue";
import moment from "moment";

export function formatDate(value) {
    if (value) {
        return moment(String(value)).format('DD/MM/YYYY HH:mm')
    }
}

Vue.filter('date', formatDate);

Vue.filter('formatTwoDigits', function (n) {
    try {
        return parseFloat(n).toLocaleString(undefined, {
            maximumFractionDigits: 2,
        });
    } catch (e) {
        return n;
    }
});

Vue.filter('fileSize', function (bytes, si = false, dp = 1) {
    const thresh = si ? 1000 : 1024;

    if (Math.abs(bytes) < thresh) {
        return bytes + ' B';
    }

    const units = si
        ? ['kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']
        : ['KiB', 'MiB', 'GiB', 'TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
    let u = -1;
    const r = 10 ** dp;

    do {
        bytes /= thresh;
        ++u;
    } while (Math.round(Math.abs(bytes) * r) / r >= thresh && u < units.length - 1);


    return bytes.toFixed(dp) + ' ' + units[u];
});
