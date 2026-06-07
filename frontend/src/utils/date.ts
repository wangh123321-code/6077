import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.locale('zh-cn')
dayjs.extend(relativeTime)

export function formatDate(date: string | Date, format: string = 'YYYY-MM-DD'): string {
  return dayjs(date).format(format)
}

export function formatDateTime(date: string | Date): string {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

export function formatRelative(date: string | Date): string {
  return dayjs(date).fromNow()
}

export function getDaysDiff(start: string | Date, end: string | Date): number {
  const startDate = dayjs(start)
  const endDate = dayjs(end)
  return endDate.diff(startDate, 'day')
}

export function getToday(): string {
  return dayjs().format('YYYY-MM-DD')
}

export function getTomorrow(): string {
  return dayjs().add(1, 'day').format('YYYY-MM-DD')
}

export function isBefore(date1: string | Date, date2: string | Date): boolean {
  return dayjs(date1).isBefore(date2)
}

export function isAfter(date1: string | Date, date2: string | Date): boolean {
  return dayjs(date1).isAfter(date2)
}

export function addDays(date: string | Date, days: number): string {
  return dayjs(date).add(days, 'day').format('YYYY-MM-DD')
}

export function getMonthRange(year: number, month: number): { start: string; end: string } {
  const start = dayjs(`${year}-${month}-01`).format('YYYY-MM-DD')
  const end = dayjs(`${year}-${month}-01`).endOf('month').format('YYYY-MM-DD')
  return { start, end }
}

export { dayjs }
