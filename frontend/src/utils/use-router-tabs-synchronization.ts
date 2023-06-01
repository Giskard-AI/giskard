import {onMounted, Ref, watch} from 'vue';
import {useRoute, useRouter} from 'vue-router/composables';


export default function useRouterTabsSynchronization(
    routeNames: string[],
    selectedValue: Ref<number | null>
) {
    const route = useRoute();
    const router = useRouter();

    watch(() => [route.name], () => onRouteUpdated());
    onMounted(() => onRouteUpdated());

    function onRouteUpdated() {
        const tab = routeNames.indexOf(route.name as string);
        if (tab >= 0) {
            selectedValue.value = tab;
        }
    }

    watch(() => selectedValue.value, (val) => onSelectedTabUpdated(val));

    function onSelectedTabUpdated(tab: number | null) {
        if (tab === null || tab === undefined) {
            return;
        }

        router.push({
            name: routeNames[tab], params: {
                ...route.params,
            }
        });
    }
}
