import Vue, {markRaw} from 'vue';
import {createPinia, PiniaVuePlugin} from "pinia";
import router from "@/router";


Vue.use(PiniaVuePlugin);
const pinia = createPinia();

pinia.use(({store}) => {
    store.$router = markRaw(router);
});

export default pinia;