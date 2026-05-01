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
    <input
      :id="param.id"
      :name="param.id"
      :type="param.type === 'number' ? 'number' : 'text'"
      class="form-control col-sm-3"
      :value="modelValue"
      :placeholder="param.value || ''"
      autocomplete="off"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <small v-if="param.description" class="form-text text-muted">{{ param.description }}</small>
  </div>
</template>
