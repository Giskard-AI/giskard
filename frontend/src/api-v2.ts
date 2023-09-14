import axios from 'axios';
import {apiURL} from '@/env';
import {getLocalHFToken, getLocalToken, removeLocalToken} from '@/utils';
import Vue from 'vue';
import {TYPE} from 'vue-toastification';
import ErrorToast from '@/views/main/utils/ErrorToast.vue';
import HuggingFaceSpacesSetupTipToast from '@/views/main/utils/HuggingFaceSpacesSetupTipToast.vue';
import router from '@/router';
import mixpanel from 'mixpanel-browser';
import {useUserStore} from '@/stores/user';
import { useMainStore } from './stores/main';
import {
    AccountControllerApi,
    CatalogControllerApi,
    Configuration,
    DatasetsControllerApi,
    DevControllerApi,
    DownloadControllerApi,
    ErrorContext,
    FeedbackControllerApi,
    GalleryUnlockControllerApi,
    InspectionControllerApi,
    LicenseControllerApi,
    Middleware,
    MlWorkerControllerApi,
    MlWorkerJobControllerApi,
    ModelControllerApi,
    ProjectControllerApi,
    PublicUserControllerApi,
    ResponseContext,
    SettingsControllerApi,
    SetupControllerApi,
    SlicingFunctionControllerApi,
    TestControllerApi,
    TestFunctionControllerApi,
    TestSuiteControllerApi,
    TransformationFunctionControllerApi,
    UploadControllerApi,
    UserAdminControllerApi,
    UserJwtControllerApi
} from "@/generated/client";


function hfRequestInterceptor(config) {
    // Do something before request is sent
    let hfToken = getLocalHFToken();
    if (hfToken && config && config.headers) {
        config.headers.Authorization = `Bearer ${hfToken}`;
    }
    return config;
}

const huggingface = axios.create();
huggingface.interceptors.request.use(hfRequestInterceptor);

function replacePlaceholders(detail: string) {
    return detail.replaceAll('GISKARD_ADDRESS', window.location.hostname);
}

async function trackError(ctx: ResponseContext, data: any) {
    let response = ctx.response;
    try {
        const trackingData = {
            method: ctx.init.method,
            code: response.status,
            message: response.statusText,
            ...data
        };
        mixpanel.track('API error', trackingData);
    } catch (e) {
        console.error('Failed to track API Error', e);
    }
}


async function errorInterceptor(context: ResponseContext): Promise<Response | void> {
    const response = context.response;
    let data: any;
    try {
        data = await response.json();
    } catch (e) {
        data = {};
    }
    await trackError(context, data);

    if (response.status === 401) {
        const userStore = useUserStore();
        removeLocalToken();
        userStore.token = '';
        userStore.isLoggedIn = false;
        if (router.currentRoute.path !== '/auth/login') {
            await router.push('/auth/login');
        }
    } else if (response.status === 503 && useMainStore().appSettings?.isDemoHfSpace) {
        console.warn(`HTTP503 received from demo space ${useMainStore().appSettings?.hfSpaceId}`);
        Vue.$toast(
            {
                component: HuggingFaceSpacesSetupTipToast,
                props: {
                    title: 'Warning',
                    detail: `You cannot modify Giskard Hugging Face demo space.
Please create your own space and get a license from Giskard.`,
                },
            },
            {
                toastClassName: 'error-toast',
                type: TYPE.WARNING,
            }
        );
    } else {
        let title: string;
        let detail: string;
        let stack: string | undefined = undefined;
        if (response.status === 502) {
            title = response.statusText;
            detail = "Error while connecting to Giskard server, check that it's running";
        } else {
            title = data.title || response.statusText;
            detail = data.detail || response.url;
            stack = data.stack;
        }

        detail = replacePlaceholders(detail);

        Vue.$toast(
            {
                component: ErrorToast,
                props: {
                    title: title || 'Error',
                    detail: detail,
                    stack: stack,
                },
            },
            {
                toastClassName: 'response-toast',
                type: TYPE.ERROR,
            }
        );
    }

    return Promise.reject(response);
}


export class APIMiddleware implements Middleware {
    async post(context: ResponseContext): Promise<Response | void> {
        if (context.response.ok) {
            return Promise.resolve(context.response)
        }
        return await errorInterceptor(context);
    }

    onError(context: ErrorContext): Promise<Response | void> {
        Vue.$toast(
            {
                component: ErrorToast,
                props: {
                    title: (context.error as any).message || 'Error',
                    detail: context.url,
                },
            },
            {
                toastClassName: 'response-toast',
                type: TYPE.ERROR,
            }
        );
        return Promise.resolve(context.response);
    }
}


const configuration = new Configuration({
    basePath: apiURL,
    accessToken: (_name?: string) => getLocalToken() || '',
    middleware: [new APIMiddleware()],
});
export const openapi = {
    settings: new SettingsControllerApi(configuration),
    projects: new ProjectControllerApi(configuration),
    account: new AccountControllerApi(configuration),
    catalog: new CatalogControllerApi(configuration),
    datasets: new DatasetsControllerApi(configuration),
    dev: new DevControllerApi(configuration),
    download: new DownloadControllerApi(configuration),
    feedback: new FeedbackControllerApi(configuration),
    galleryUnlock: new GalleryUnlockControllerApi(configuration),
    inspection: new InspectionControllerApi(configuration),
    license: new LicenseControllerApi(configuration),
    mlWorker: new MlWorkerControllerApi(configuration),
    mlWorkerJob: new MlWorkerJobControllerApi(configuration),
    model: new ModelControllerApi(configuration),
    project: new ProjectControllerApi(configuration),
    publicUser: new PublicUserControllerApi(configuration),
    setup: new SetupControllerApi(configuration),
    slicingFunction: new SlicingFunctionControllerApi(configuration),
    test: new TestControllerApi(configuration),
    testFunction: new TestFunctionControllerApi(configuration),
    testSuite: new TestSuiteControllerApi(configuration),
    transformationFunction: new TransformationFunctionControllerApi(configuration),
    upload: new UploadControllerApi(configuration),
    userAdmin: new UserAdminControllerApi(configuration),
    userJwt: new UserJwtControllerApi(configuration),
};
