import { reactive } from 'vue';
import { Client } from '@stomp/stompjs';

export const state = reactive({
  workerStatus: {}
});


const client = new Client({
  brokerURL: 'ws://localhost:9000/websocket',
  onConnect: () => {
    client.subscribe('/topic/worker-status', message =>
      state.workerStatus = JSON.parse(message.body).connected
    );
  }
});

client.activate();
