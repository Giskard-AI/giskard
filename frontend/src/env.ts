const env = process.env.VUE_APP_ENV;

export const apiURL = `${process.env.VUE_APP_DOMAIN}` || window.location.origin;
export const appName = process.env.VUE_APP_NAME;