const env = import.meta.env.VITE_APP_ENV;

export const apiURL = `${import.meta.env.VITE_APP_DOMAIN}` || window.location.origin;
console.log('VITE_APP_DOMAIN: ', import.meta.env.VITE_APP_DOMAIN);
export const appName = import.meta.env.VITE_APP_NAME;

