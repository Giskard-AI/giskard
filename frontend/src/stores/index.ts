import Vue from 'vue';
import {createPinia, PiniaVuePlugin} from "pinia";



Vue.use(PiniaVuePlugin);
const pinia = createPinia();


export default pinia;