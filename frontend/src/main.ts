// import './assets/main.css'
// import './styles/global.scss';
// import './styles/colors.scss';

import {createApp, markRaw} from 'vue'
import {createPinia} from 'pinia'

import App from './App.vue'
import router from './router'

import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

import {createVuetify} from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import {setupMixpanel} from "@/tracking";
import Toast, {POSITION} from "vue-toastification";
import {ToastOptions} from "vue-toastification/dist/types/types";
import {createVfm} from 'vue-final-modal'
import {aliases, mdi} from 'vuetify/iconsets/mdi'

const vuetify = createVuetify({
    components,
    directives,
    icons: {
        defaultSet: 'mdi',
        aliases,
        sets: {
            mdi,
        },
    },
})

const options: ToastOptions = {
    // transition: "Vue-Toastification__fade",
    timeout: 5000,
    closeOnClick: false,
    hideProgressBar: true,
    draggable: false,
    position: POSITION.BOTTOM_CENTER,
    // filterBeforeCreate: (toast, toasts) => {
    //
    //     if (toasts.filter(
    //         t => {
    //             return t.content.toString() === toast.content.toString();
    //         }
    //     ).length !== 0) {
    //         // Returning false discards the toast
    //         return false;
    //     }
    //     // You can modify the toast if you want
    //     return toast;
    // }
}

const vfm = createVfm()
const pinia = createPinia();

pinia.use(({store}) => {
    store.$router = markRaw(router)
});


const app = createApp(App)

app.use(pinia)
app.use(router)
app.use(vuetify)
app.use(Toast, options)
app.use(vfm)


setupMixpanel();

app.mount('#app')
