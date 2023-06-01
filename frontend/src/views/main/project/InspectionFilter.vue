<template>
  <v-menu
      v-model="menu"
      :close-on-content-click="false"
      disable-keys
      offset-x right
      :nudge-left="dirtyFilterValue.type === RowFilterType.CUSTOM ? 1000 : 300"
      :nudge-bottom="28"
      :max-width="dirtyFilterValue.type === RowFilterType.CUSTOM ? 1000 : 300"
      min-width="300"
  >
    <template v-slot:activator="{ on, attrs }">
      <v-btn
          outlined
          tile
          small
          v-bind="attrs"
          v-on="on"
      >
        <v-icon left>
          {{ filter.type === RowFilterType.ALL ? 'mdi-filter-outline' : 'mdi-filter' }}
        </v-icon>
        {{ filterTypesByKey[filter.type].label }}
      </v-btn>
    </template>

    <v-form @submit.p.prevent="save">
      <v-card>
        <v-row no-gutters>
          <v-col v-if="dirtyFilterValue.type === RowFilterType.CUSTOM" class="left-column d-flex"
                 @keydown.tab="e=>e.stopPropagation()"
          >
            <CustomInspectionFilter
                :is-target-available="isTargetAvailable"
                :labels="labels"
                :model-type="modelType"
                v-model="dirtyFilterValue"
            />
          </v-col>
          <v-col class="right-column">
            <v-list dense class="pa-0">
              <v-list-item
                  @click="selectFilter(item)"
                  class="tile"
                  :class="{'selected': dirtyFilterValue.type === item.value}"
                  v-for="item in filterTypes"
                  :key="item.value"
                  :disabled="item.disabled"
                  link
              >
                <v-list-item-title>{{ item.label }}</v-list-item-title>
              </v-list-item>
            </v-list>
          </v-col>
        </v-row>

        <v-card-actions class="actions-section" v-show="dirtyFilterValue.type === RowFilterType.CUSTOM">
          <v-spacer></v-spacer>

          <v-btn
              text
              @click="menu = false"
          >
            Cancel
          </v-btn>
          <v-btn
              color="primary"
              text
              type="submit"
          >
            Save
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-form>
  </v-menu>

</template>

<script lang="ts">
import Component from "vue-class-component";
import Vue from "vue";
import {isClassification} from "@/ml-utils";
import {Prop, Watch} from "vue-property-decorator";
import {Filter, ModelType, RowFilterType} from "@/generated-sources";
import CustomInspectionFilter from "./CustomInspectionFilter.vue";
import _ from "lodash";
import mixpanel from "mixpanel-browser";
import {anonymize} from "@/utils";

interface FilterType {
  label: string;
  value: RowFilterType;
  disabled?: boolean;
  description?: string;
}

@Component({components: {CustomInspectionFilter}})
export default class InspectionFilter extends Vue {
    RowFilterType = RowFilterType;
    @Prop({required: true}) modelType!: ModelType;
    @Prop({required: true}) inspectionId!: number;
    @Prop({default: false}) isTargetAvailable!: boolean;
    @Prop({required: true}) labels!: string[];

    menu = false;

    @Watch('menu')
    onMenuChange(nv) {
        if (nv) {
            this.dirtyFilterValue = _.cloneDeep(this.filter);
        }
    }


    filterTypes: FilterType[] = [
        {value: RowFilterType.ALL, label: 'All', description: 'Entire dataset'},
        {
            value: RowFilterType.CORRECT,
            label: isClassification(this.modelType) ? 'Correct Predictions' : 'Closest predictions (top 15%)',
            disabled: !this.isTargetAvailable,
            description: isClassification(this.modelType) ?
          'Predicted value is equal to actual value in dataset target column' :
          'Top 15% of most accurate predictions'
        },
        {
            value: RowFilterType.WRONG,
            label: isClassification(this.modelType) ? 'Incorrect Predictions' : 'Most distant predictions (top 15%)',
            disabled: !this.isTargetAvailable
        },
        {value: RowFilterType.BORDERLINE, label: 'Borderline', disabled: !this.isTargetAvailable},
        {value: RowFilterType.CUSTOM, label: 'Custom'}
    ];
    filterTypesByKey = _.keyBy(this.filterTypes, e => e.value);
    dirtyFilterValue: Filter = this.initFilter();
    filter: Filter = this.initFilter();

    private initFilter(): Filter {
        return {
            inspectionId: this.inspectionId,
            type: RowFilterType.ALL
        }
    }

    mounted() {
        this.$emit('input', this.filter); // send an initial value outside
    }

    selectFilter(filter: FilterType) {
        if (this.dirtyFilterValue) {
            this.dirtyFilterValue.type = filter.value;
            if (this.dirtyFilterValue.type !== RowFilterType.CUSTOM) {
                this.save();
      }
    }
  }

  save() {
    this.menu = false;
    this.filter = _.cloneDeep(this.dirtyFilterValue);
    if (this.filter) {
      mixpanel.track('Inspection filter', {
        'selectedFilter': this.filter.type,
        'minThreshold': this.filter.minThreshold,
        'maxThreshold': this.filter.maxThreshold,
        'maxDiffThreshold': this.filter.maxDiffThreshold,
        'minDiffThreshold': this.filter.minDiffThreshold,
        'targetLabel': anonymize(this.filter.targetLabel),
        'predictedLabel': anonymize(this.filter.predictedLabel),
        'thresholdLabel': anonymize(this.filter.thresholdLabel),
      });
    }
    this.$emit('input', this.filter);
  }
}
</script>

<style scoped lang="scss">
@import "src/styles/colors.scss";

.right-column {
  max-width: 300px;
  min-width: 300px;
}

.left-column {
  min-width: 700px;
  border-right: 1px solid lightgrey;
}

.v-list-item__title {
  white-space: break-spaces;
}

.actions-section {
  border-top: 1px solid lightgrey;
}

.tile {
  cursor: pointer;

  &.selected {
    background: $selected;
    color: $color-giskard-main !important;
  }

  &:hover {
    background: $hover;
  }
}

.filter-description {
  color: lightgrey;
  font-weight: 0;
}

</style>
