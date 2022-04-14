<template>
  <div class="d-flex">
    <div v-show="!editable">{{ label }}</div>
    <v-text-field v-show="editable" v-model="label"></v-text-field>
    <v-icon class="mode-switch" @click="editable=!editable">edit</v-icon>
  </div>

</template>

<script lang="ts">
import Component from "vue-class-component";
import {Prop, Vue} from "vue-property-decorator";

@Component
export default class EditableLabel extends Vue {
  @Prop() label?: string;
  editable = false;

}
</script>

<style scoped lang="scss">
@import "/src/styles/colors.scss";

.mode-switch {
  &:hover {
    cursor: pointer;
    color: $color-giskard-main;
  }
}
</style>