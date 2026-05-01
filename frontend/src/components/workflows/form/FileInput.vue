<script setup>
import { ref } from 'vue'

const props = defineProps({
  param: { type: Object, required: true },
  multiple: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue'])

const fileInput = ref(null)
const fileName = ref('')
const files = ref([])

function onFileChange(e) {
  if (props.multiple) {
    files.value = Array.from(e.target.files)
    emit('update:modelValue', files.value)
  } else {
    const f = e.target.files[0] || null
    fileName.value = f?.name || ''
    emit('update:modelValue', f)
  }
}

function removeFile(idx) {
  files.value.splice(idx, 1)
  emit('update:modelValue', [...files.value])
}

function removeAll() {
  files.value = []
  if (fileInput.value) fileInput.value.value = ''
  emit('update:modelValue', [])
}
</script>

<template>
  <div class="mb-3">
    <label class="form-label">
      {{ param.label }}
      <span v-if="param.required" class="text-danger">*</span>
    </label>

    <template v-if="!multiple">
      <div class="input-group col-sm-3">
        <input
          type="text"
          class="form-control"
          :value="fileName"
          readonly
          placeholder="No file selected"
        />
        <button type="button" class="btn btn-outline-secondary" @click="fileInput.click()">
          Browse
        </button>
      </div>
    </template>

    <template v-else>
      <div class="mb-2">
        <button type="button" class="btn btn-outline-secondary btn-sm me-2" @click="fileInput.click()">
          <i class="fas fa-plus me-1"></i>Select Files
        </button>
        <button v-if="files.length" type="button" class="btn btn-outline-danger btn-sm" @click="removeAll">
          Remove All
        </button>
      </div>
      <ul v-if="files.length" class="list-group mb-2" style="max-width: 400px;">
        <li
          v-for="(f, i) in files"
          :key="i"
          class="list-group-item d-flex justify-content-between align-items-center py-1"
        >
          <small>{{ f.name }}</small>
          <button type="button" class="btn btn-sm btn-link text-danger p-0" @click="removeFile(i)">
            <i class="fas fa-times"></i>
          </button>
        </li>
      </ul>
    </template>

    <input
      ref="fileInput"
      :name="param.id"
      type="file"
      class="d-none"
      :multiple="multiple"
      @change="onFileChange"
    />
    <small v-if="param.description" class="form-text text-muted">{{ param.description }}</small>
  </div>
</template>
