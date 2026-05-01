<script setup>
defineProps({
  param: { type: Object, required: true },
  modelValue: { type: String, default: '' },
})
defineEmits(['update:modelValue'])
</script>

<template>
  <div class="mb-3">
    <label class="form-label">
      {{ param.label }}
      <span v-if="param.required" class="text-danger">*</span>
    </label>
    <div
      v-for="(opt, i) in param.values"
      :key="opt.key ?? opt"
      class="form-check"
    >
      <input
        :id="`${param.id}_${i}`"
        :name="param.id"
        type="radio"
        class="form-check-input"
        :value="opt.key ?? opt"
        :checked="(opt.key ?? opt) === modelValue"
        @change="$emit('update:modelValue', $event.target.value)"
      />
      <label :for="`${param.id}_${i}`" class="form-check-label">
        {{ opt.label ?? opt }}
      </label>
    </div>
    <small v-if="param.description" class="form-text text-muted">{{ param.description }}</small>
  </div>
</template>
