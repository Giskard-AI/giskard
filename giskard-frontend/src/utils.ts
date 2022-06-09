import {UserDTO} from '@/generated-sources';

export const getLocalToken = (): string | null => localStorage.getItem('token');

export const saveLocalToken = (token: string) => localStorage.setItem('token', token);

export const removeLocalToken = () => localStorage.removeItem('token');

export const getUserFullDisplayName = (user: UserDTO): string => {
    return user.displayName ? `${user.displayName} (${user.user_id})` : user.user_id;
}

export const toSlug = (str: string): string =>{
   return str.toLowerCase()
        .trim()
        .replace(/[^\w-]+/g, '-')           // Replace spaces with -
        .replace(/[\s]+/g, '')       // Remove all non-word chars
        .replace(/(^-|-$)+/g, '')       // Remove pipe
        .replace(/(-{2,})+/g, '-');        // Replace multiple - with single -
}