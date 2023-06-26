import {reactive} from 'vue';
import {Client} from '@stomp/stompjs';
import {apiURL} from './env';
import {getLocalToken, httpUrlToWsUrl} from './utils';
import {useMainStore} from './stores/main';
import {TYPE} from 'vue-toastification';

export const state = reactive({
  workerStatus: {
    connected: false,
  },
});
let jwtToken = getLocalToken() || "";
export const client = new Client({
  connectHeaders: {jwt: jwtToken},
  brokerURL: httpUrlToWsUrl(apiURL) + '/websocket',
  onConnect: () => {
    client.subscribe('/topic/worker-status', message => {
      const data = JSON.parse(message.body);

      if (!state.workerStatus.connected && data.connected) {
        useMainStore().addNotification({
          content: 'ML Worker is connected!',
          color: TYPE.SUCCESS,
        });
      }

      if (state.workerStatus.connected && !data.connected) {
        useMainStore().addNotification({
          content: 'ML Worker is disconnected!',
          color: TYPE.ERROR,
        });
      }

      state.workerStatus.connected = data.connected;
    });
  },
});
