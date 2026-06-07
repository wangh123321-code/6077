<template>
  <div class="date-picker">
    <el-date-picker
      v-model="dates"
      type="daterange"
      :start-placeholder="startPlaceholder"
      :end-placeholder="endPlaceholder"
      :disabled-date="disabledDate"
      :shortcuts="shortcuts"
      range-separator="至"
      value-format="YYYY-MM-DD"
      @change="handleChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { getToday, addDays } from '@/utils/date'

const props = withDefaults(
  defineProps<{
    modelValue?: [string, string]
    startPlaceholder?: string
    endPlaceholder?: string
    minDate?: string
  }>(),
  {
    startPlaceholder: '入住日期',
    endPlaceholder: '离店日期',
    minDate: ''
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: [string, string] | null]
  change: [value: [string, string] | null]
}>()

const dates = ref<[string, string] | null>(props.modelValue || null)

watch(
  () => props.modelValue,
  (val) => {
    dates.value = val
  }
)

const shortcuts = [
  {
    text: '今天入住',
    value: () => {
      const start = getToday()
      const end = addDays(start, 1)
      return [new Date(start), new Date(end)]
    }
  },
  {
    text: '明天入住',
    value: () => {
      const start = addDays(getToday(), 1)
      const end = addDays(start, 1)
      return [new Date(start), new Date(end)]
    }
  },
  {
    text: '周末入住',
    value: () => {
      const now = new Date()
      const day = now.getDay()
      const diffToFriday = day === 0 ? 6 : 5 - day
      const start = addDays(getToday(), Math.max(0, diffToFriday))
      const end = addDays(start, 2)
      return [new Date(start), new Date(end)]
    }
  }
]

function disabledDate(time: Date) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  if (props.minDate) {
    const min = new Date(props.minDate)
    min.setHours(0, 0, 0, 0)
    return time < min
  }

  return time < today
}

function handleChange(value: [string, string] | null) {
  emit('update:modelValue', value)
  emit('change', value)
}
</script>

<style scoped lang="scss">
.date-picker {
  width: 100%;

  :deep(.el-date-editor) {
    width: 100%;
  }
}
</style>
