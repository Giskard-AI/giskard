import {onMounted, Ref, watch} from 'vue';
import {useRoute, useRouter} from 'vue-router/composables';


export default function useRouterParamSynchronization<T>(
    routeName: string,
    param: string,
    values: T[],
    selectedValue: Ref<T | null>,
    id: string
) {
    const route = useRoute();
    const router = useRouter();

    watch(() => [route.name, route.params], () => onRouteUpdated());
    onMounted(() => onRouteUpdated());

    function onRouteUpdated() {
        if (route.name === routeName) {
            const executionId = Number(route.params[param]);
            selectedValue.value = values?.find(execution => execution[id] === executionId) ?? null;
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
