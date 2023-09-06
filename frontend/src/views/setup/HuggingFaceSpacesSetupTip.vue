<template>
  <v-container class="mt-7 vertical-container">
    <v-card max-width="800" class="mt-6 mb-4 card-step">
      <v-card-title class="font-weight-medium">
        Welcome to Giskard Gallery on Hugging Face Spaces 🤗
      </v-card-title>
      <v-card-text>
        You are currently in Giskard's demo instance on Hugging Face Spaces. You can try out the functionnalities of Giskard using our demo projects:
          <ul>
            <li>Running test suites</li>
            <li>Adding more tests</li>
            <li>Debugging models</li>
          </ul>
        To test your own model, please create your own Giskard instance.
      </v-card-text>
    </v-card>
    <p class="text-center">To create <span class="font-weight-bold">your own Giskard instance on Hugging Face Spaces</span>, follow these steps:</p>
    <v-card max-width="800" class="mt-6 mb-4 card-step">
        <v-card-title class="font-weight-medium">
          <v-icon class="mr-2" color="primary">mdi-numeric-1-circle-outline</v-icon>
          <span>Duplicate this Space</span>
          <v-spacer></v-spacer>
        </v-card-title>
        <v-card-text>
          Click on the
          <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" aria-hidden="true" role="img" class="p-0.5" width="1em" height="1em" preserveAspectRatio="xMidYMid meet" viewBox="0 0 32 32">
            <circle cx="16" cy="7" r="3" fill="currentColor"></circle>
            <circle cx="16" cy="16" r="3" fill="currentColor"></circle>
            <circle cx="16" cy="25" r="3" fill="currentColor"></circle>
          </svg>
          button in the navigation bar of Hugging Face Spaces, and choose
          "
          <svg class="mr-2 text-gray-700 " aria-hidden="true" fill="currentColor" focusable="false" role="img" width="1em" height="1em" viewBox="0 0 32 26" preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">
            <path fill-rule="evenodd" clip-rule="evenodd" d="M18.5769 0.524814C18.5769 0.234967 18.8126 0 19.1034 0C26.2306 0 32.0001 5.81162 32.0001 12.9704C32.0001 20.1292 26.2306 25.9408 19.1034 25.9408C18.8126 25.9408 18.5769 25.7058 18.5769 25.416C18.5769 25.1261 18.8126 24.8912 19.1034 24.8912C25.64 24.8912 30.9472 19.5586 30.9472 12.9704C30.9472 6.38217 25.64 1.04963 19.1034 1.04963C18.8126 1.04963 18.5769 0.81466 18.5769 0.524814Z" fill="currentcolor"></path>
            <path fill-rule="evenodd" clip-rule="evenodd" d="M13.0034 26C20.1849 26 26.0067 20.1965 26.0067 13.0375C26.0067 5.87847 20.1849 0.0749512 13.0034 0.0749512C5.82181 0.0749512 0 5.87847 0 13.0375C0 20.1965 5.82181 26 13.0034 26ZM13.0656 7.51757C13.6455 7.51757 14.1155 7.98615 14.1155 8.56418V12.0529H17.6152C18.1951 12.0529 18.6651 12.5215 18.6651 13.0995C18.6651 13.6775 18.1951 14.1461 17.6152 14.1461H14.1155V17.6348C14.1155 18.2129 13.6455 18.6815 13.0656 18.6815C12.4857 18.6815 12.0157 18.2129 12.0157 17.6348V14.1461H8.51598C7.93613 14.1461 7.46606 13.6775 7.46606 13.0995C7.46606 12.5215 7.93613 12.0529 8.51598 12.0529H12.0157V8.56418C12.0157 7.98615 12.4857 7.51757 13.0656 7.51757Z" fill="currentcolor" fill-opacity="0.65"></path>
          </svg>Duplicate this Space"
          to start.
        </v-card-text>
        <v-card-title class="font-weight-medium">
          <v-icon class="mr-2" color="primary">mdi-numeric-2-circle-outline</v-icon>
          <span>Choose your hardware</span>
          <v-spacer></v-spacer>
        </v-card-title>
        <v-card-text>
          To setup your own Giskard instance on Hugging Face Spaces, you need to set the owner, Space name, visibility and choose the hardware.
          We recommend to use paid hardware for better performance.
          <br/>
          We also recommend to setup a paid <a href="https://huggingface.co/docs/hub/spaces-storage#persistent-storage" target="_blank">persistent storage</a> to avoid your personal data loss across restarting or upgrading.
          <!-- But you can also use a free hardware. Keep in mind that without interactions after <a href="https://huggingface.co/docs/hub/spaces-gpus#sleep-time" target="_blank">sleep time</a>, the Space will be closed. Your data will be lost without a persistent storage. -->
        </v-card-text>
        <v-card-title class="font-weight-medium">
          <v-icon class="mr-2" color="primary">mdi-numeric-3-circle-outline</v-icon>
          <span>Upload your license</span>
          <v-spacer></v-spacer>
        </v-card-title>
        <v-card-text>
          After your Space entering running status, you will see Giskard's setup page to request and upload your Giskard's license.
          <!-- To avoid uploading your license after restarting or upgrading, we recommend to setup "GISKARD_LICENSE" with your obtained license in your <a href="https://huggingface.co/docs/hub/spaces-overview#managing-secrets" target="_blank">secrets</a> from Hugging Face Spaces settings. -->
        </v-card-text>
    </v-card>
    <p class="text-center">You can also deploy Giskard on <span class="font-weight-bold">Cloud (AWS, GCP, Azure, etc.) or on-premise</span> by following <a href="https://docs.giskard.ai/en/latest/guides/installation_app/index.html" target="_blank">Giskard's documentation</a>.</p>
  </v-container>
</template>

<script setup lang="ts">

</script>
<style scoped>
</style>
