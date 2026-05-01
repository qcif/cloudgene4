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
    <select
      :id="param.id"
      :name="param.id"
      class="form-select col-sm-3"
      :value="modelValue"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <option
        v-for="opt in param.values"
        :key="opt.key ?? opt"
        :value="opt.key ?? opt"
      >
        {{ opt.label ?? opt }}
      </option>
    </select>
    <small v-if="param.description" class="form-text text-muted">{{ param.description }}</small>
  </div>
</template>
