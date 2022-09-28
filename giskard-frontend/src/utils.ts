import {UserDTO} from '@/generated-sources';
import * as _ from "lodash";
import {readUserProfile} from "@/store/main/getters";
import {Role} from "@/enums";
import * as crypto from "crypto-js";

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

function anonymizeString(str: string): string {
    let res = crypto.SHA1(str);
    return res.toString().substring(0, 10);
}

export function anonymize(obj: any) {
    if (_.isNil(obj)){
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

/** 
 * Returning the n first chars of s ... n last chars of s
 */
export function abbreviateMiddle(s: string, n: number, max_size: number){
    if (s.length > max_size)
        return s.slice (0, n) + '...' +  s.slice(-n)
    return s
}

export function isAdmin(store) {
    return readUserProfile(store)?.roles!.includes(Role.ADMIN)
}