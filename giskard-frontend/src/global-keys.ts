import Mousetrap from 'mousetrap';
import { getLocalToken } from '@/utils';
import { commitAddNotification } from '@/store/main/mutations';
import store from '@/store';

Mousetrap.bind('@ j j', async () => {
  let localToken = getLocalToken();
  if (localToken) {
    await navigator.clipboard.writeText(localToken);
    commitAddNotification(store, { content: 'Copied JWT token to clipboard', color: '#262a2d' });
  }
});