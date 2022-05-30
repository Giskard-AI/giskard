<template>
  <v-form @submit.prevent="">
    <ValidationObserver ref="observer" v-slot="{ invalid }">
      <v-container fluid>
        <v-card-title>
          Create new test
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols=12>
              <ValidationProvider name="Test name" mode="eager" rules="required" v-slot="{errors}">
                <v-text-field label="Test name" v-model="name" :error-messages="errors"></v-text-field>
              </ValidationProvider>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer/>
          <v-btn tile small class="primary" @click="submit" :disabled="invalid">Create</v-btn>
        </v-card-actions>
      </v-container>
    </ValidationObserver>
  </v-form>

</template>

<script lang="ts">
import Component from "vue-class-component";
import Vue from "vue";
import {Prop} from "vue-property-decorator";
import {api} from "@/api";
import ModelSelector from "@/views/main/utils/ModelSelector.vue";
import {format} from 'date-fns'
import { ModelDTO } from '@/generated-sources';


@Component({
  components: {ModelSelector}
})
export default class TestCreateModal extends Vue {
  @Prop({required: true}) suiteId!: number;
  public name: string = "Test-" + format(new Date(), 'yyyy.MM.dd HH:mm');
  model: ModelDTO | null = null;

  public async submit() {
    let createdTestSuite = await api.createTest(this.suiteId, this.name);
    this.$emit('submit', createdTestSuite)
  }
}
</script>

<style scoped lang="scss">

</style>