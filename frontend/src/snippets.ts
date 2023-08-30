import {useMainStore} from "@/stores/main";
import {apiURL} from "@/env";
import {useApiKeyStore} from "@/stores/api-key-store";

const mainStore = useMainStore();
const apiKeyStore = useApiKeyStore();
export async function generateGiskardClientSnippet(hfToken=null) {
    let apiKey: string;
    if (apiKeyStore.getFirstApiKey) {
        apiKey = apiKeyStore.getFirstApiKey;
    } else {
        apiKey = '<Generate your API Key first>';
    }
    const isRunningOnHF = mainStore.appSettings!.isRunningOnHfSpaces;

    let snippet = `
# Create a Giskard client
client = giskard.GiskardClient(
    url="${apiURL}",  # URL of your Giskard instance
    token="${apiKey}"`;

    if (isRunningOnHF && hfToken) {
        snippet += `,
    hf_token="${hfToken}"`;
    }
    snippet += `)
`;
    return snippet;
}