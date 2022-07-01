import {UserDTO} from '@/generated-sources';
import * as _ from "lodash";
import {readUserProfile} from "@/store/main/getters";
import {Role} from "@/enums";

export const getLocalToken = (): string | null => localStorage.getItem('token');

export const saveLocalToken = (token: string) => localStorage.setItem('token', token);

export const removeLocalToken = () => localStorage.removeItem('token');

export const getUserFullDisplayName = (user: UserDTO): string => {
    return user.displayName ? `${user.displayName} (${user.user_id})` : user.user_id;
}

export const toSlug = (str: string): string => {
    return str.toLowerCase()
        .trim()
        .replace(/[^\w-]+/g, '-')           // Replace spaces with -
        .replace(/\s+/g, '')       // Remove all non-word chars
        .replace(/(^-|-$)+/g, '')       // Remove pipe
        .replace(/(-{2,})+/g, '-');        // Replace multiple - with single -
}

async function anonymizeString(str: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(str);
    const hashBuffer = await crypto.subtle.digest('SHA-1', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer))
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}

export async function anonymize(obj: any) {
    if (_.isArray(obj)) {
        return Promise.all(obj.map(anonymize));
    } else if (_.isObject(obj)) {
        const ret = {}
        for (const k of Object.keys(obj)) {
            ret[k] = await anonymize(obj[k]);
        }
        return ret;
    } else {
        return anonymizeString(obj.toString());
    }
}
export function isAdmin(store){
    return readUserProfile(store)?.roles!.includes(Role.ADMIN)
}