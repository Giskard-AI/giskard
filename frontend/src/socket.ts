import { reactive } from 'vue';
import { Client } from '@stomp/stompjs';
import { apiURL } from './env';
import { httpUrlToWsUrl } from './utils';

export const state = reactive({
  workerStatus: {
    connected: false,
  },
});

const client = new Client({
  brokerURL: httpUrlToWsUrl(apiURL) + '/websocket',
  onConnect: () => {
    client.subscribe('/topic/worker-status', message => {
      const data = JSON.parse(message.body);
      state.workerStatus.connected = data.connected;
    });
  },
});

client.activate();
