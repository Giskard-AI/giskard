import { reactive } from 'vue';

import io from 'socket.io-client';
import { apiURL } from '@/env';

export const state = reactive({
  workerStatus: {},
});

export const socket = io(apiURL, {
  transports: ['websocket'],
});

socket.on('worker-status', (data: any) => {
  state.workerStatus = data;
});
