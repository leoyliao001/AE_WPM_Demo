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
  overflow-x: hidden;
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

/* Atmosphere pages scroll internally (like Welcome); keep edge color matched */
.app-main:has(.welcome-page),
.app-main:has(.page-shell--atmosphere),
.app-main:has(.intake-page--atmosphere) {
  background: #dff3fa;
  overflow: hidden;
}

.app-main:has(.welcome-page--plain),
.app-main:has(.page-shell--plain),
.app-main:has(.intake-page--plain) {
  background: #fff;
}

/* Handsontable pages: page owns scroll via Handsontable only */
.app-main:has(.fpo-page),
.app-main:has(.po-page),
.app-main:has(.gsc-page),
.app-main:has(.oa-page) {
  overflow: hidden;
}
</style>
