import { AxiosResponse } from 'axios';
import { State } from './store/state';
import { Store } from 'vuex';
import { commitAddNotification, commitRemoveNotification } from '@/store/main/mutations';
import { readToken } from "@/store/main/getters";

export function dialogDownloadFile(response: AxiosResponse, fileName: string) {
  const fileURL = window.URL.createObjectURL(new Blob([response.data]));
  const fileLink = document.createElement('a');
  fileLink.href = fileURL;
  fileLink.setAttribute('download', fileName);
  document.body.appendChild(fileLink);
  fileLink.click();
}

export async function performApiActionWithNotif(store: Store<State>,
  apiAction: () => any,
  callbackFn: () => any,
) {
  const loadingNotification = { content: 'Please wait...', showProgress: true };
  try {
    commitAddNotification(store, loadingNotification);
    const response = await apiAction();
    callbackFn();
    commitRemoveNotification(store, loadingNotification);
    commitAddNotification(store, { content: response.message, color: 'success'});
  } catch (error) {
    commitRemoveNotification(store, loadingNotification);
    commitAddNotification(store, { content: error.response.detail, color: 'error' });
  }
}