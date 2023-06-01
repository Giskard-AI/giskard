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

    function onRouteUpdated() {
        if (route.name === routeName && values.value !== undefined) {
            const executionId = Number(route.params[param]);

            selectedValue.value = values.value.find(execution => execution[id] === executionId) ?? null;
        }
    }

    watch(() => selectedValue.value, (val) => onSelectedValueUpdated(val));

    function onSelectedValueUpdated(val: T | null) {
        if (val === null || val === undefined || route.params[param] === val[id].toString(10)) {
            return;
        }

        router.push({
            name: routeName, params: {
                ...route.params,
                [param]: val[id].toString(10)
            }
        });
    }
}
