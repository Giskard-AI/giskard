import {useMainStore} from "@/stores/main";
import {api} from "@/api";
import {apiURL} from "@/env";

const mainStore = useMainStore();

export async function generateGiskardClientSnippet(hfToken=null) {
    const giskardToken = await api.getApiAccessToken();
    const isRunningOnHF = mainStore.appSettings!.isRunningOnHfSpaces;

    let snippet = `
# Create a Giskard client
client = giskard.GiskardClient(
    url="${apiURL}",  # URL of your Giskard instance
    token="${giskardToken?.id_token}"`;

    if (isRunningOnHF && hfToken) {
        snippet += `,
    hf_token="${hfToken}"`;
    }
    snippet += `)
`;
    return snippet;
}