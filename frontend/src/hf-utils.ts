import {api} from '@/api';
import {useMainStore} from '@/stores/main';


export async function fetchHFSpacesToken() {
    if (useMainStore().appSettings!.isRunningOnHfSpaces) {
        try {
            const res = await api.getHuggingFaceSpacesToken(useMainStore().appSettings?.hfSpaceId!!);
            return res.data.token;
        } catch(error) {
            if (error.response.status == 401) {
                console.warn("Running in a private Hugging Face space, may need an access token.")
                return null;
            }
        }
    }
    return null;
}

export async function attemptFetchHFSpacesToken(then, error) {
    const token = await fetchHFSpacesToken();
    if (token) {
        if (then) {
            then(token);
        }
    } else {
        if (error) {
            error();
        }
    }
}
