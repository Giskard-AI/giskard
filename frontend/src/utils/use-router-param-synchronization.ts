import {onMounted, Ref, watch} from 'vue';
import {useRoute, useRouter} from 'vue-router/composables';


export default function useRouterParamSynchronization<T>(
    routeName: string,
    param: string,
    values: Ref<T[] | undefined>,
    selectedValue: Ref<T | null>,
    id: string
) {
    const route = useRoute();
    const router = useRouter();

    watch(() => [route.name, route.params, values.value], () => onRouteUpdated());
    onMounted(() => onRouteUpdated());

    async function onRouteUpdated() {
        if (route.name === routeName && values.value !== undefined) {
            const routeId = Number(route.params[param]);

            if (Number.isNaN(routeId)) {
                await router.push({name: routeName, params: {[param]: values.value[0][id]}});
                return;
            }

            selectedValue.value = values.value.find(execution => execution[id] === routeId) ?? null;
        }
    }

}
