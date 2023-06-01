import Mousetrap from 'mousetrap';
import {getLocalToken} from '@/utils';
import {commitAddNotification} from '@/store/main/mutations';
import store from '@/store';

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
    let localToken = getLocalToken();
    if (localToken) {
        copyToClipboard(localToken).then(() => {
            commitAddNotification(store, {content: 'Copied JWT token to clipboard', color: '#262a2d'});
        });
    }
});