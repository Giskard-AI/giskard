import {UserDTO} from '@/generated-sources';
import * as _ from "lodash";
import {Role} from "@/enums";
import * as crypto from "crypto-js";
import {useUserStore} from "@/stores/user";

export const getLocalToken = (): string | null => localStorage.getItem('token');

export const saveLocalToken = (token: string) => localStorage.setItem('token', token);

export const removeLocalToken = () => localStorage.removeItem('token');

export const getUserFullDisplayName = (user: UserDTO): string => {
    return user.displayName ? `${user.displayName} (${user.user_id})` : user.user_id;
}

export const toSlug = (str: string): string => {
    return str.toLowerCase()
        .trim()
        .replace(/[^\w-]+/g, '_')           // Replace spaces with _
        .replace(/\s+/g, '')       // Remove all non-word chars
        .replace(/(^-|-$)+/g, '')       // Remove pipe
        .replace(/(_{2,})+/g, '_');        // Replace multiple _ with single _
}

function anonymizeString(str: string): string {
    let res = crypto.SHA1(str);
    return res.toString().substring(0, 10);
}

export function anonymize(obj: any) {
    if (_.isNil(obj)) {
        return obj;
    }
    try {
        if (_.isArray(obj)) {
            return obj.map(anonymize);
        } else if (_.isObject(obj)) {
            const ret = {}
            for (const k of Object.keys(obj)) {
                ret[k] = anonymize(obj[k]);
            }
            return ret;
        } else {
            return anonymizeString(obj.toString());
        }
    } catch (e) {
        console.error(`Failed to anonymize data ${obj}, falling back to empty value`, e)
        return null;
    }
}

export function isAdmin(store) {
    const userStore = useUserStore();
    return userStore.userProfile?.roles!.includes(Role.ADMIN)
}

function stringHash(str: string) {
    let hash = 0, i, chr;
    if (str === undefined || str.length === 0) return hash;

    for (i = 0; i < str.length; i++) {
        chr = str.charCodeAt(i);
        hash = ((hash << 5) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    return hash;
}

export function pasterColor(str: string) {
    const hue = stringHash(str) % 360;
    return `hsl(${hue}, 70%, 90%)`;
}