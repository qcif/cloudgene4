<script setup>
const props = defineProps({
  currentPage: { type: Number, required: true },
  totalPages: { type: Number, required: true },
})
const emit = defineEmits(['change'])

function pages() {
  const p = []
  for (let i = 1; i <= props.totalPages; i++) p.push(i)
  return p
}
</script>

<template>
  <nav v-if="totalPages > 1" aria-label="Pagination">
    <ul class="pagination justify-content-center">
      <li class="page-item" :class="{ disabled: currentPage <= 1 }">
        <button class="page-link" @click="$emit('change', currentPage - 1)">&larr; Previous</button>
      </li>
      <li
        v-for="p in pages()"
        :key="p"
        class="page-item"
        :class="{ active: p === currentPage }"
      >
        <button class="page-link" @click="$emit('change', p)">{{ p }}</button>
      </li>
      <li class="page-item" :class="{ disabled: currentPage >= totalPages }">
        <button class="page-link" @click="$emit('change', currentPage + 1)">Next &rarr;</button>
      </li>
    </ul>
  </nav>
</template>
