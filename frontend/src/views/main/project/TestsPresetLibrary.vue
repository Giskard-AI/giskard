<template>
  <div>Tests preset</div>
</template>
<script>
import axios from "axios";
import {apiUrlJava} from "@/env";
import {api} from "@/api";
import {IAppInitData} from "@/interfaces";

export default {
  name: 'TestsPresetLibrary',
  async mounted() {
    let axiosResponse = await api.getMe();

    function foo() {
      // let headers = {
      //   headers: {
      //     Authorization: `Bearer ${getLocalToken()}`,
      //   },
      // };
      // console.log(headers);
      return axios.get<IAppInitData>(`${apiUrlJava}/api/v2/users/me`);
    }

    let b = await foo();
    debugger
  }
}
</script>
