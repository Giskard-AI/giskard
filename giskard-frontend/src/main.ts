import './global-keys'
import '@babel/polyfill';
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
