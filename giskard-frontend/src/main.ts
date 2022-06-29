import './global-keys'
import "core-js/stable";
import "regenerator-runtime/runtime";
// Import Component hooks before component definitions
import './component-hooks';
import Vue from 'vue';
import vuetify from './plugins/vuetify';
import './plugins/vee-validate';
import App from './App.vue';
import router from './router';
import store from '@/store';
import './registerServiceWorker';
import 'vuetify/dist/vuetify.min.css';
import 'vuetify-dialog/dist/vuetify-dialog.css';
import './styles/global.scss';
import './styles/colors.scss';
import './filters'

import Toast, {POSITION} from "vue-toastification";
// Import the CSS or use your own!
import "vue-toastification/dist/index.css";
import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
import {library} from '@fortawesome/fontawesome-svg-core'
import {faUserSecret} from '@fortawesome/free-solid-svg-icons'
import mixpanel from 'mixpanel-browser';

Vue.config.productionTip = false;

new Vue({
    router,
    store,
    vuetify,
    render: (h) => h(App)
}).$mount('#app');

library.add(faUserSecret)
Vue.component('font-awesome-icon', FontAwesomeIcon)


Vue.use(Toast, {
    transition: "Vue-Toastification__fade",
    timeout: 5000,
    closeOnClick: false,
    hideProgressBar: true,
    draggable: false,
    position: POSITION.BOTTOM_CENTER,
    filterBeforeCreate: (toast, toasts) => {

        if (toasts.filter(
            t => {
                return t.content.toString() === toast.content.toString();
            }
        ).length !== 0) {
            // Returning false discards the toast
            return false;
        }
        // You can modify the toast if you want
        return toast;
    }
});
const isDev = process.env.NODE_ENV === 'development';
const devProjectKey = '4cca5fabca54f6df41ea500e33076c99';
const prodProjectKey = '2c3efacc6c26ffb991a782b476b8c620';

mixpanel.init(isDev ? devProjectKey : prodProjectKey, {
    debug: isDev,
    api_host: "https://tracker.giskard.ai",
});
