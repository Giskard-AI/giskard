<template>
  <div>
    <v-toolbar flat dense light>
      <v-toolbar-title class="text-h6 font-weight-regular secondary--text text--lighten-1">
        Users
      </v-toolbar-title>
      <v-spacer></v-spacer>
      <v-text-field
        v-model="searchTerm"
        label="Search"
        single-line
        hide-details
        outlined
        dense
        clearable
        class="shrink"
        append-icon="mdi-magnify"
      ></v-text-field>
      <v-checkbox dense v-model="showInactive" label="Show inactive" class="pt-4 mx-1"></v-checkbox>

      <v-tooltip bottom :disabled="canAddUsers">
        <template v-slot:activator="{ on}">
          <div v-on="on">

            <v-btn small tile color="primary" to="/main/admin/users/invite" class="mx-1"
                   :disabled="!canAddUsers">
              <v-icon left>send</v-icon>
              Invite
            </v-btn>
            <v-btn small tile color="primary" to="/main/admin/users/create" class="mx-1"
                   :disabled="!canAddUsers">
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
        <span v-for='r in item.roles'>{{r | roleName}}</span>
      </template>
      <template v-slot:item.enabled="{item}">
        <v-icon v-if="item.enabled">checkmark</v-icon>
        <v-icon v-else>close</v-icon>
      </template>
      <template v-slot:item.action="{item}" v-slot:item.id="{item}">
        <v-btn icon slot="activator" :to="{name: 'main-admin-users-edit', params: {id: item.id}}">
          <v-icon color="primary">edit</v-icon>
        </v-btn>
        <v-btn icon @click="deleteUser(item)">
          <v-icon color="accent">delete</v-icon>
        </v-btn>
      </template>
    </v-data-table>
    </v-container>
  </div>
</template>

<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
import { readAdminUsers } from '@/store/admin/getters';
import { dispatchGetUsers, dispatchDeleteUser } from '@/store/admin/actions';
import {readAppSettings} from "@/store/main/getters";

@Component
export default class AdminUsers extends Vue {

  public searchTerm: string = "";
  public showInactive: boolean = false;
  public canAddUsers: boolean = true;

  get headers() {
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
      filter: value => this.showInactive || value
    },
    {
      text: 'Role',
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
  }

  get users() {
    return readAdminUsers(this.$store);
  }

  public async mounted() {
    await dispatchGetUsers(this.$store);
    const appSettings = await readAppSettings(this.$store);
    this.canAddUsers = !appSettings || !appSettings.seats_available || appSettings.seats_available > 0;
  }

  public async deleteUser(user) {
    if (await this.$dialog.confirm({
      text: `Are you sure you want to delete user <strong>${user.user_id}</strong>?`,
      title: 'Delete user'
    })) {
      await dispatchDeleteUser(this.$store, {id: user.user_id});
    }
  }
}
</script>
