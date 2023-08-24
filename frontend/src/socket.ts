import { reactive } from 'vue';
import { Client, Frame } from '@stomp/stompjs';
import { apiURL } from './env';
import { getLocalToken, httpUrlToWsUrl } from './utils';
import { useMainStore } from './stores/main';
import { TYPE } from 'vue-toastification';

export const state = reactive({
  workerStatus: {
    connected: undefined,
  },
});
export const client = new Client({
  onStompError: async (frame: Frame) => {
    if (frame.headers.message.includes('AccessDeniedException') || frame.headers.message.includes('.ExpiredJwtException')) {
      await client.deactivate();
      useMainStore().addNotification({content: "Failed to establish websocket connection.", color: TYPE.ERROR});
      console.error(`Failed to establish websocket connection: ${frame.headers.message}`);
    }
  },
  beforeConnect: () => {
    client.connectHeaders = {jwt: getLocalToken() || ""};
  },
  brokerURL: httpUrlToWsUrl(apiURL) + '/websocket',
  onConnect: () => {
    client.subscribe('/topic/worker-status', message => {
      const data = JSON.parse(message.body);

      if (state.workerStatus.connected === false && data.connected === true) {
        useMainStore().addNotification({
          content: 'ML Worker is connected!',
          color: TYPE.SUCCESS,
        });
      }

      if (state.workerStatus.connected === true && data.connected === false) {
        useMainStore().addNotification({
          content: 'ML Worker is disconnected!',
          color: TYPE.ERROR,
        });
      }

      state.workerStatus.connected = data.connected;
    });
  },
});
