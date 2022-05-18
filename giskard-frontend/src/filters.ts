import Vue from "vue";
import moment from "moment";

Vue.filter('date', function (value) {
    if (value) {
        return moment(String(value)).format('DD/MM/YYYY hh:mm')
    }
});

Vue.filter('formatTwoDigits', function (n) {
    try {
        return parseFloat(n).toLocaleString(undefined, {
            maximumFractionDigits: 2,
        });
    } catch (e) {
        return n;
    }
});