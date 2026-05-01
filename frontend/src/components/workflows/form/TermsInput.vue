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
      :required="param.required"
      :checked="modelValue"
      @change="$emit('update:modelValue', $event.target.checked)"
    />
    <label :for="param.id" class="form-check-label col-sm-10" v-html="param.label"></label>
    <div class="invalid-feedback">You must accept the terms to continue.</div>
  </div>
</template>
