import { defineStore } from "pinia";
import { api } from "@/api";
import { useMainStore } from "./main";
import { getLocalHFToken } from "@/utils";


interface HFSpacesTokenState {
    token: string | null,
    expire: Date,
    publicSpace: boolean,
}

export const useHFSpacesTokenStore = defineStore('hfSpacesToken', {
    state: (): HFSpacesTokenState => ({
        token: null,
        expire: new Date(),
        publicSpace: true,
    }),
    actions: {
        async getHFSpacesToken() {
            const now = new Date();
            if (now < this.expire) {
                // Not yet expired
                return this.token;
            }

            // Fetch new HFSpaces token
            try {
                const res = await api.getHuggingFaceSpacesToken(useMainStore().appSettings?.hfSpaceId!!);
                this.token = res.data.token;
                this.expire = new Date();
                this.expire.setDate(this.expire.getDate() + 1); // Expire in 24 hours

                if (getLocalHFToken() !== null) {
                    // Fetched with HF Access token
                    this.publicSpace = false;
                }
            } catch(error) {
                if (error.response.status == 401) {
                    console.warn("Running in a private Hugging Face space, may need an access token.")
                    this.publicSpace = false;
                    this.token = null;
                }
            }
            return this.token;
        },
    }
});
