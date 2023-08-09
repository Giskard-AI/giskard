<template>
  <div v-if="mainStore.authAvailable">
    <v-toolbar flat dense light>
      <v-spacer></v-spacer>
      <v-text-field v-model="searchTerm" label="Search" single-line hide-details outlined dense clearable class="shrink" append-icon="mdi-magnify"></v-text-field>
      <v-checkbox dense v-model="showInactive" label="Show inactive" class="pt-4 mx-1"></v-checkbox>

      <v-tooltip bottom :disabled="canAddUsers">
        <template v-slot:activator="{ on }">
          <div v-on="on">

            <v-btn small tile color="primary" to="/main/admin/users/invite" class="mx-1" :disabled="!canAddUsers">
              <v-icon left>send</v-icon>
              Invite
            </v-btn>
            <v-btn small tile color="primary" to="/main/admin/users/create" class="mx-1" :disabled="!canAddUsers">
              <v-icon left>add_circle</v-icon>
              Create
            </v-btn>
          </div>
        </template>

        <span>You've reached the maximum number of users available with the current license</span>
      </v-tooltip>
    </v-toolbar>

    <v-container fluid>
      <v-data-table height="75vh" fixed-header :headers="headers" :items="users" sort-by="id" :search="searchTerm">
        <!-- eslint-disable vue/valid-v-slot vue/no-unused-vars-->
        <template v-slot:item.roles="{ item }">
          <v-chip small v-for='r in item.roles'>{{ r | roleName }}</v-chip>
        </template>
        <template v-slot:item.enabled="{ item }">
          <v-icon v-if="item.enabled">checkmark</v-icon>
          <v-icon v-else>close</v-icon>
        </template>
        <template v-slot:item.action='{ item }' v-slot:item.id='{item}'>
          <v-tooltip bottom>
            <template v-slot:activator="{ on }">
              <v-btn icon v-on="on" slot='activator' :to="{ name: 'main-admin-users-edit', params: { id: item.id } }">
                <v-icon color='primary'>edit</v-icon>
              </v-btn>
            </template>
            <span>Edit</span>
          </v-tooltip>
          <v-tooltip v-if="item.enabled" bottom>
            <template v-slot:activator="{ on }">
              <v-btn v-on="on" icon @click='disableUser(item)'>
                <v-icon color='accent'>mdi-account-cancel</v-icon>
              </v-btn>
            </template>
            <span>Disable</span>
          </v-tooltip>
          <v-tooltip v-else bottom>
            <template v-slot:activator="{ on }">
              <v-btn v-on="on" icon @click='enableUser(item)'>
                <v-icon color='warning'>restore</v-icon>
              </v-btn>
            </template>
            <span>Restore</span>
          </v-tooltip>
          <v-tooltip v-if="!item.enabled" bottom>
            <template v-slot:activator="{ on }">
              <v-btn v-on="on" icon @click='deleteUser(item)'>
                <v-icon color='accent'>delete</v-icon>
              </v-btn>
            </template>
            <span>Delete</span>
          </v-tooltip>
        </template>
      </v-data-table>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useAdminStore } from '@/stores/admin';
import { useMainStore } from '@/stores/main';
import { AdminUserDTO } from '@/generated-sources';
import AdminUserDTOWithPassword = AdminUserDTO.AdminUserDTOWithPassword;

const adminStore = useAdminStore();
const mainStore = useMainStore();

const searchTerm = ref<string>("");
const showInactive = ref<boolean>(false);

const headers = computed(() => {
  return [
    {
      text: 'id',
      sortable: true,
      value: 'id',
      align: 'left',
    },
    {
      text: 'User ID',
      sortable: true,
      value: 'user_id',
      align: 'left',
    },
    {
      text: 'Email',
      sortable: true,
      value: 'email',
      align: 'left',
    },
    {
      text: 'Display Name',
      sortable: true,
      value: 'displayName',
      align: 'left',
    },
    {
      text: 'Enabled',
      value: 'enabled',
      align: 'left',
      filter: value => showInactive.value || value
    },
    {
      text: 'Roles',
      sortable: true,
      filterable: false,
      value: 'roles',
      align: 'left',
    },
    {
      sortable: false,
      filterable: false,
      text: 'Actions',
      value: 'action'
    }
  ]
});

const users = computed(() => {
  return adminStore.users;
});

const canAddUsers = computed(() => {
  return users.value.filter(u => u.activated).length < mainStore.license?.userLimit;
});

onMounted(async () => {
  await adminStore.getUsers();
});

async function disableUser(user: AdminUserDTOWithPassword) {
  await adminStore.disableUser(user);
}

async function deleteUser(user: AdminUserDTOWithPassword) {
  await adminStore.deleteUser(user);
}

async function enableUser(user: AdminUserDTOWithPassword) {
  await adminStore.enableUser(user);
}

</script>
