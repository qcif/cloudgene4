<script setup>
defineProps({
  param: { type: Object, required: true },
  modelValue: { type: String, default: '' },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <div class="mb-3">
    <label :for="param.id" class="form-label">
      {{ param.label }}
      <span v-if="param.required" class="text-danger">*</span>
    </label>
    <textarea
      :id="param.id"
      :name="param.id"
      class="form-control col-sm-3"
      :rows="param.rows || 6"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
    ></textarea>
    <small v-if="param.description" class="form-text text-muted">{{ param.description }}</small>
  </div>
</template>
