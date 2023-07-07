<template>
  <v-main>
    <v-container fluid fill-height class="pa-0">
      <v-row class="fill-height">
        <v-col cols="12" md="6">
          <v-container fluid fill-height class="pa-0">
            <v-row align-content="center" justify="center">
              <div>
                <div class="d-flex justify-center mb-6">
                  <img src="@/assets/logo_v2_full.png" alt="logo" width="240">
                </div>
                <router-view></router-view>
              </div>
            </v-row>
          </v-container>
        </v-col>
        <v-col cols="12" md="6" class="background">
        </v-col>
      </v-row>
    </v-container>
  </v-main>
</template>

<script setup lang="ts">
</script>

<style>
.background {
  background-image: url("~@/assets/wallpaper.jpg");
  background-position: 95% 20%;
  background-size: auto 100%;
}
</style>
