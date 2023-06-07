<template>
    <vue-final-modal
        v-slot="{ close }"
        v-bind="$attrs"
        classes="modal-container"
        content-class="modal-content"
        v-on="$listeners"
    >
        <div class="text-center">
            <ValidationObserver ref="observer" v-slot="{ invalid, pristine }">
                <v-card>
                    <v-card-title>
                        Create an alias for {{ props.name }}
                    </v-card-title>
                    <v-card-text class="card-content">
                        <ValidationProvider name="Alias" rules="required|aliasDoesNotExists" v-slot="{errors}">
                            <v-text-field label="Alias" autofocus v-model="aliasName" :error-messages="errors"
                                          outlined/>
                        </ValidationProvider>
                    </v-card-text>
                    <v-card-actions>
                        <v-btn @click="close" color="error">Cancel</v-btn>
                        <v-btn @click="() => saveAlias(close)" color="primary" :disabled="invalid">Create</v-btn>
                    </v-card-actions>
                </v-card>
            </ValidationObserver>
        </div>
    </vue-final-modal>
</template>

<script setup lang="ts">

import {useTestSuiteStore} from "@/stores/test-suite";
import {computed, ref} from "vue";
import {chain} from "lodash";
import {extend} from "vee-validate";
import {FunctionInputDTO} from '@/generated-sources';

const props = defineProps<{
    name: string,
    type: string,
}>();

const aliasName = ref<string>('')

const {suite} = useTestSuiteStore();

const emit = defineEmits(['save']);

const existingAliases = computed(() => chain([
        ...suite!.functionInputs,
        ...chain(suite!.tests)
            .flatMap(test => Object.values(test.functionInputs))
            .filter(input => input.isAlias)
            .value()
    ])
        .map('value')
        .uniq()
        .value()
)

const aliasDoesNotExists = {
    message() {
        return 'Alias is already existing'
    },
    validate(value) {
        return !existingAliases.value.includes(value);
    }
}

extend('aliasDoesNotExists', aliasDoesNotExists);

function saveAlias(close) {
    emit('save', {
        isAlias: true,
        name: props.name,
        type: props.type,
        value: aliasName.value
    } as FunctionInputDTO)
    close()
}

</script>

<style scoped>
::v-deep(.modal-container) {
    display: flex;
    justify-content: center;
    align-items: center;
}

::v-deep(.modal-content) {
    position: relative;
    display: flex;
    flex-direction: column;
    margin: 0 1rem;
    padding: 1rem;
    min-width: 50vw;
    max-height: 80vh;
    overflow: auto;

}

.card-content {
    text-align: start;
}

</style>
