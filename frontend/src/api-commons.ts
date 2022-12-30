import {AxiosResponse} from 'axios';
import {State} from './store/state';
import {Store} from 'vuex';
import {useMainStore} from "@/stores/main";

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
  const mainStore = useMainStore();
  const loadingNotification = { content: 'Please wait...', showProgress: true };
  try {
    mainStore.addNotification(loadingNotification);
    const response = await apiAction();
    callbackFn();
    mainStore.removeNotification(loadingNotification);
    mainStore.addNotification({ content: response.message, color: 'success'});
  } catch (error) {
    mainStore.removeNotification(loadingNotification);
    mainStore.addNotification({ content: error.response.detail, color: 'error' });
  }
}