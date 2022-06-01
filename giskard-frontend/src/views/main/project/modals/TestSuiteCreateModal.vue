<template>
  <v-form @submit.prevent="">
    <ValidationObserver ref="observer" v-slot="{ invalid }">

      <v-container fluid>
        <v-card-title>
          Create new test suite
        </v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols=12>
              <ValidationProvider name="Test suite name" mode="eager" rules="required" v-slot="{errors}">
                <v-text-field label="Test suite name" v-model="name" :error-messages="errors"></v-text-field>
              </ValidationProvider>
              <ValidationProvider name="Model" mode="eager" rules="required" v-slot="{errors}">
                <ModelSelector :project-id="projectId" :value.sync="model"/>
              </ValidationProvider>
              <ValidationProvider name="Reference dataset" v-slot="{errors}">
                <DatasetSelector :project-id="projectId" :value.sync="referenceDS" :label="'Reference dataset'"/>
              </ValidationProvider>
              <ValidationProvider name="Actual dataset" v-slot="{errors}">
                <DatasetSelector :project-id="projectId" :value.sync="actualDS" :label="'Actual dataset'"/>
              </ValidationProvider>
              <v-switch v-model="shouldCreateAutoTests" :label="'Create tests automatically'"></v-switch>
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
import {ModelDTO} from '@/generated-sources';
import DatasetSelector from "@/views/main/utils/DatasetSelector.vue";

@Component({
  components: {DatasetSelector, ModelSelector}
})
export default class TestSuiteCreateModal extends Vue {
  @Prop({required: true}) projectId!: number;
  public name: string = "";
  model: ModelDTO | null = null;
  referenceDS: ModelDTO | null = null;
  actualDS: ModelDTO | null = null;
  shouldCreateAutoTests: boolean = true;

  public async submit() {
    let createdTestSuite = await api.createTestSuite({
      name: this.name,
      projectId: this.projectId,
      referenceDatasetId: this.referenceDS && this.referenceDS.id,
      actualDatasetId: this.actualDS && this.actualDS.id,
      modelId: this.model!.id,
      shouldGenerateTests: this.shouldCreateAutoTests
    });
    this.$emit('submit', createdTestSuite)
  }
}
</script>

<style scoped lang="scss">

</style>