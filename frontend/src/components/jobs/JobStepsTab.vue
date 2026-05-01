<script setup>
defineProps({ job: { type: Object, required: true } })

const typeClass = {
  0: 'text-success',
  1: 'text-danger',
  2: 'text-warning',
  3: 'text-primary',
  4: 'text-danger font-monospace',
}

const stepStateClass = (step) => {
  if (step.state === 'completed') return 'step-completed'
  if (step.state === 'running') return 'step-running'
  if (step.state === 'failed') return 'step-failed'
  return ''
}
</script>

<template>
  <div v-if="job.steps && job.steps.length">
    <div
      v-for="step in job.steps"
      :key="step.id"
      class="step-item"
      :class="stepStateClass(step)"
    >
      <div class="d-flex align-items-center mb-1">
        <i
          v-if="step.state === 'running'"
          class="fas fa-spinner fa-spin me-2 text-primary"
        ></i>
        <i
          v-else-if="step.state === 'completed'"
          class="fas fa-check me-2 text-success"
        ></i>
        <i
          v-else-if="step.state === 'failed'"
          class="fas fa-times me-2 text-danger"
        ></i>
        <strong>{{ step.name }}</strong>
      </div>
      <div v-if="step.messages" class="ms-3">
        <div
          v-for="(msg, i) in step.messages"
          :key="i"
          class="small mb-1"
          :class="typeClass[msg.type] || ''"
        >
          <span v-if="msg.type === 3" class="spinner-border spinner-border-sm me-1"></span>
          <span v-if="msg.type === 4"><pre class="mb-0">{{ msg.text }}</pre></span>
          <span v-else>{{ msg.text }}</span>
        </div>
      </div>
    </div>
  </div>
  <p v-else class="text-muted"><i>No step information available.</i></p>
</template>
