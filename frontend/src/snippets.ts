import {useMainStore} from "@/stores/main";
import axios from "axios";
import {api} from "@/api";
import {apiURL} from "@/env";

const mainStore = useMainStore();

async function fetchHFToken() {
    const isRunningOnHF = mainStore.appSettings!.isRunningOnHfSpaces;
    if (isRunningOnHF) {
        const res = await axios.get(`https://huggingface.co/api/spaces/${mainStore.appSettings?.hfSpaceId}/jwt`);
        return res.data.token;
    }
}

export async function generateGiskardClientSnippet() {
    const giskardToken = await api.getApiAccessToken();
    const isRunningOnHF = mainStore.appSettings!.isRunningOnHfSpaces;
    let hfToken: any;
    if (isRunningOnHF) {
        hfToken = await api.getHuggingFaceToken(mainStore.appSettings!.hfSpaceId);

        const res = await axios.get(`https://huggingface.co/api/spaces/${mainStore.appSettings?.hfSpaceId}/jwt`);
        hfToken.value = res.data.token;
    }

    let snippet = `
# Create a Giskard client
client = giskard.GiskardClient(
    url="${apiURL}",  # URL of your Giskard instance
    token="${giskardToken?.id_token}"`;

    if (isRunningOnHF) {
        snippet += `,
    hf_token="${hfToken?.value}"`;
    }
    snippet += `)
`;
    return snippet;
}