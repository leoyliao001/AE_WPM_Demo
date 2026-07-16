<style>
* {
  box-sizing: border-box;
}

html,
body,
#app {
  height: 100%;
  margin: 0;
}

body {
  background: #fff;
  font-family: 'Maersk Text', sans-serif;
  overflow: hidden;
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
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.app-main {
  display: flex;
  flex: 1;
  flex-direction: column;
  min-height: 0;
  overflow: auto;
}

/* FPO Mapping: page owns scroll via Handsontable only */
.app-main:has(.fpo-page) {
  overflow: hidden;
}
</style>
