<template>
  <v-dialog v-model="opened" width="300">
    
    <template v-slot:activator="{ on, attrs }">
        <v-btn tile small class="primary ml-2" v-bind="attrs" v-on="on" :disabled="disabledButton">Save</v-btn>
    </template>

    <v-card>
        <v-card-title>
            {{title}}
        </v-card-title>
        <v-card-text>
            {{text}}
        </v-card-text>
        <v-card-actions>
            <v-spacer></v-spacer>
            <v-btn color="secondary" text @click="opened = false;">
            Cancel
            </v-btn>
            <v-btn color="accent" text @click="opened = false; $emit('ok');">
            Ok
            </v-btn>
        </v-card-actions>
    </v-card>
    </v-dialog>
</template>


<script setup lang="ts">

import {ref} from "vue";

interface Props {
  text: string,
  title: string,
  disabledButton: boolean
}

const props = withDefaults(defineProps<Props>(), {
  text: '', title: 'Are you sure?', disabledButton: false
});

const opened = ref<boolean>(false);

</script>

<!--<script>-->
<!--export default {-->
<!--    props: {-->
<!--        text: {type: String, default: ''},-->
<!--        title: {type: String, default: 'Are you sure?'},-->
<!--        disabledButton: {type: Boolean, default: false}-->
<!--    },-->
<!--    data() {-->
<!--        return {-->
<!--            opened: false-->
<!--        }-->
<!--    }-->
<!--}-->
<!--</script>    -->
<style>

</style>