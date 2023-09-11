import Mousetrap from 'mousetrap';
import {useMainStore} from "@/stores/main";
import {api} from "@/api";

export function copyToClipboard(textToCopy) {
    // navigator clipboard api needs a secure context (https)
    if (navigator.clipboard && window.isSecureContext) {
        // navigator clipboard api method'
        return navigator.clipboard.writeText(textToCopy);
    } else {
        // text area method
        let textArea = document.createElement('textarea');
        textArea.value = textToCopy;
        // make the textarea out of viewport
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        return new Promise((res, rej) => {
            // here the magic happens
            document.execCommand('copy') ? res(undefined) : rej();
            textArea.remove();
        });
    }
}

Mousetrap.bind('@ j j', () => {
    const mainStore = useMainStore();
    api.getApiKeys().then(keys => {
        if (keys.length) {
            let firstKey = keys[0].key;
            copyToClipboard(firstKey).then(() => {
                mainStore.addNotification({content: `Copied API key to clipboard: ${firstKey}`});
            });
        } else {
            mainStore.addNotification({content: 'No API keys found'});
        }
    })
});