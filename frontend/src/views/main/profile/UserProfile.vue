<template>
  <div class="fill-height d-flex flex-column">
    <v-toolbar flat dense light class="flex-grow-0">
      <v-toolbar-title class="text-h6 font-weight-regular secondary--text text--lighten-1">
        My Profile
      </v-toolbar-title>
    </v-toolbar>
    <v-container class="flex-grow-1 overflow-y-auto" fluid>
      <v-row v-if="userProfile">
        <v-col>
          <v-card height="100%">
            <ValidationObserver ref="observer" v-slot="{ invalid, pristine }">
              <v-form @submit.prevent="">
                <v-card-title class="font-weight-light secondary--text">User details</v-card-title>
                <v-card-text>
                  <v-row>
                    <v-col cols=6>
                      <div>
                        <div class="caption secondary--text text--lighten-3">User ID</div>
                        <div class="subtitle-1">{{ userProfile.user_id }}</div>
                      </div>
                      <div class="mt-3">
                        <div class="caption secondary--text text--lighten-3">Display Name</div>
                        <div v-if="!editModeToggle">
                          <div class="subtitle-1" v-if="userProfile.displayName">{{ userProfile.displayName }}</div>
                          <div class="subtitle-1" v-else>(not set)</div>
                        </div>
                        <div v-else>
                          <ValidationProvider name="Display name" mode="eager" rules="min:4" v-slot="{errors}">
                            <v-text-field v-model="displayName" single-line :error-messages="errors"
                                          class="my-0 py-0"></v-text-field>
                          </ValidationProvider>
                        </div>
                      </div>
                    </v-col>
                    <v-col cols=6>
                      <div>
                        <div class="caption secondary--text text--lighten-3">Roles</div>
                        <div class="subtitle-1" v-for='role in userProfile.roles'>{{ role | roleName }}</div>
                      </div>
                      <div class="mt-3">
                        <div class="caption secondary--text text--lighten-3">Email</div>
                        <div v-if="!editModeToggle" class="subtitle-1">{{ userProfile.email }}</div>
                        <div v-else>
                          <ValidationProvider name="Email" mode="eager" rules="required|email" v-slot="{errors}">
                            <v-text-field type="email" v-model="email" single-line hide :error-messages="errors"
                                          class="my-0 py-0"></v-text-field>
                          </ValidationProvider>
                        </div>
                      </div>
                    </v-col>
                  </v-row>
                </v-card-text>
                <v-card-actions class="px-4 pb-4">
                  <v-btn tile small color="accent" to="/main/profile/password">Change password</v-btn>
                  <v-spacer></v-spacer>
                  <v-btn tile small class="primary" v-show="!editModeToggle" @click="editModeToggle = true">Edit
                  </v-btn>
                  <v-btn tile small class="secondary" v-show="editModeToggle"
                         @click="editModeToggle = false; resetFormData();">Cancel
                  </v-btn>
                  <ButtonModalConfirmation
                      v-if="editModeToggle"
                      :disabledButton="invalid || pristine"
                      @ok="submit">
                  </ButtonModalConfirmation>
                </v-card-actions>
              </v-form>
            </ValidationObserver>
          </v-card>
        </v-col>
        <v-col>
          <ApiTokenCard/>
        </v-col>
      </v-row>
      <v-row v-if="isAdmin">
        <v-col>
          <RunningWorkerJobs/>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import {computed, ref} from "vue";
import {UpdateMeDTO} from "@/generated-sources";
import {Role} from "@/enums";
import ApiTokenCard from "@/components/ApiTokenCard.vue";
import RunningWorkerJobs from '@/views/main/profile/RunningWorkerJobs.vue';

import {useUserStore} from "@/stores/user";
import {useMainStore} from "@/stores/main";

const userStore = useUserStore();
const mainStore = useMainStore();

const displayName = ref<string>("");
const email = ref<string>("");
const editModeToggle = ref<boolean>(false);
const isAdmin = ref<boolean>(false);

const observer = ref<any | null>(null);

function resetFormData() {
  const userProfile = userStore.userProfile;
  if (userProfile) {
    if (userProfile.displayName) {
      displayName.value = userProfile.displayName;
    }
    email.value = userProfile.email;
    isAdmin.value = userProfile.roles!.includes(Role.ADMIN);
  }
}

resetFormData();

const userProfile = computed(() => {
  return userStore.userProfile;
});

function submit() {
  (observer.value as any).validate().then(() => {
    const currentProfile = userStore.userProfile;
    const updatedProfile: UpdateMeDTO = {};
    if (displayName.value && displayName.value !== currentProfile?.displayName) {
      updatedProfile.displayName = displayName.value;
    }
    if (email.value && email.value !== currentProfile?.email) {
      updatedProfile.email = email.value;
    }
    if (Object.keys(updatedProfile).length > 0) {
      userStore.updateUserProfile(updatedProfile).then(() => {
        editModeToggle.value = false;
        resetFormData();
      });
    } else {
      editModeToggle.value = false;
      resetFormData();
    }
  });
}
</script>

<style lang="scss" scoped>
.worker-tabs {
  width: auto;
  flex-grow: 0;
}

.token-area-wrapper {
  background-color: rgba(211, 211, 211, 0.52);
  padding: 10px;
}

.divider {
  margin-top: 10px;
  margin-bottom: 10px;
}

.token-area {
  user-select: all;
  word-break: break-all;
  font-size: 0.75em;
  font-family: monospace;
}

.worker-tab {
  display: flex;
  justify-content: space-between;
  width: 120px;
}

.giskard-address {
  border: 1px lightgrey dashed;
  padding: 2px;
}
</style>
