<script setup>
defineProps({
  type: { type: String, default: 'danger' },
  message: { type: String, default: '' },
})
</script>

<template>
  <div v-if="message" :class="`alert alert-${type}`" role="alert">
    {{ message }}
  </div>
</template>
