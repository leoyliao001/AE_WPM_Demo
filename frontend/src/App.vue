<style>
* {
  box-sizing: border-box;
}

body {
  background: #fff;
  font-family: 'Maersk Text', sans-serif;
  margin: 0;
}
</style>

<template>
  <div class="app-layout">
    <AppHeader />
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import AppHeader from './components/AppHeader.vue'
</script>

<style scoped>
.app-layout {
  background: #fff;
  min-height: 100vh;
}

.app-main {
  min-height: calc(100vh - 56px);
}
</style>
