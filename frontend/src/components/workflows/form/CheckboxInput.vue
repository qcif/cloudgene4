<script setup>
defineProps({
  param: { type: Object, required: true },
  modelValue: { type: Boolean, default: false },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <div class="mb-3 form-check">
    <input
      :id="param.id"
      :name="param.id"
      type="checkbox"
      class="form-check-input"
      :checked="modelValue"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <label :for="param.id" class="form-check-label">
      {{ param.label }}
    </label>
    <small v-if="param.description" class="d-block form-text text-muted">{{ param.description }}</small>
  </div>
</template>
