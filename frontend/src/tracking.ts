import mixpanel from "mixpanel-browser";
import _ from "lodash";
import {Directive} from "vue";

export function setupMixpanel() {
    const isDev = import.meta.env.VITE_ENV === 'development';
    const devProjectKey = '4cca5fabca54f6df41ea500e33076c99';
    const prodProjectKey = '2c3efacc6c26ffb991a782b476b8c620';

    mixpanel.init(isDev ? devProjectKey : prodProjectKey, {
        debug: isDev,
        api_host: "https://pxl.giskard.ai",
        opt_out_tracking_by_default: true
    });
}

export const trackClick: Directive = {
    mounted: (el, binding) => {
        el.addEventListener("click", () => {
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
    }
}