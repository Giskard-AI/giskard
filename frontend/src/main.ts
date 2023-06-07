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
import './registerServiceWorker';
// import 'vuetify/dist/vuetify.min.css';
import 'vuetify-dialog/dist/vuetify-dialog.css';
import './filters'

import Toast, {POSITION} from "vue-toastification";
import {FontAwesomeIcon} from "@fortawesome/vue-fontawesome";
import {library} from '@fortawesome/fontawesome-svg-core'
import {faUserSecret} from '@fortawesome/free-solid-svg-icons'
import mixpanel from 'mixpanel-browser';
import _ from "lodash";

import './styles/global.scss';
import './styles/colors.scss';
import vfmPlugin from 'vue-final-modal'
import pinia from "@/stores";
import VueMoment from "vue-moment";
import VuetifyDialog from "vuetify-dialog";

Vue.config.productionTip = false;

Vue.use(vfmPlugin);

new Vue({
    router,
    vuetify,
    pinia,
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
Vue.use(VueMoment);
Vue.use(VuetifyDialog, {
    context: {
        vuetify
    }
})

export function setupMixpanel() {
    const isDev = process.env.NODE_ENV === 'development';
    const devProjectKey = '4cca5fabca54f6df41ea500e33076c99';
    const prodProjectKey = '2c3efacc6c26ffb991a782b476b8c620';

    mixpanel.init(isDev ? devProjectKey : prodProjectKey, {
        debug: isDev,
        api_host: "https://pxl.giskard.ai",
        opt_out_tracking_by_default: true
    });
    Vue.directive('trackClick', {
        inserted: (el, binding, _vnode) => {
            el.addEventListener("click", (_evt) => {
                try {
                    if (_.isString(binding.value)) {
                        mixpanel.track(binding.value);
                    } else if (_.isObject(binding.value)) {
                        // @ts-ignore
                        mixpanel.track(binding.value.name, binding.value.data);
                    }
                } catch (e) {
                    console.error("Failed to track event", binding.value, e);
                }
            });
        },
    })

}

setupMixpanel();
