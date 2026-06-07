import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { CatRoom, Service } from '@/types'
import { getBookingPrice } from '@/api/booking'
import { formatDate, getDaysDiff } from '@/utils/date'

export const useBookingStore = defineStore('booking', () => {
  const selectedCatRoom = ref<CatRoom | null>(null)
  const selectedServices = ref<Service[]>([])
  const checkInDate = ref<string>('')
  const checkOutDate = ref<string>('')
  const catInfo = ref({
    name: '',
    breed: '',
    age: 0,
    specialRequirements: ''
  })
  const priceInfo = ref({
    totalPrice: 0,
    roomPrice: 0,
    servicePrice: 0,
    discount: 0
  })
  const loading = ref(false)
  const bookedDates = ref<string[]>([])

  const nights = computed(() => {
    if (!checkInDate.value || !checkOutDate.value) return 0
    return Math.max(1, getDaysDiff(checkInDate.value, checkOutDate.value))
  })

  const calculatedRoomPrice = computed(() => {
    if (!selectedCatRoom.value || nights.value <= 0) return 0
    return selectedCatRoom.value.price * nights.value
  })

  const calculatedServicePrice = computed(() => {
    return selectedServices.value.reduce((sum, s) => sum + s.price, 0)
  })

  const calculatedTotalPrice = computed(() => {
    return calculatedRoomPrice.value + calculatedServicePrice.value - priceInfo.value.discount
  })

  const isValid = computed(() => {
    return (
      selectedCatRoom.value &&
      checkInDate.value &&
      checkOutDate.value &&
      catInfo.value.name &&
      catInfo.value.breed &&
      catInfo.value.age > 0
    )
  })

  const isCatInfoValid = computed(() => {
    return (
      catInfo.value.name &&
      catInfo.value.breed &&
      catInfo.value.age > 0
    )
  })

  watch(
    [selectedCatRoom, checkInDate, checkOutDate, selectedServices],
    () => {
      updateLocalPrice()
    },
    { deep: true }
  )

  function updateLocalPrice() {
    priceInfo.value.roomPrice = calculatedRoomPrice.value
    priceInfo.value.servicePrice = calculatedServicePrice.value
    priceInfo.value.totalPrice = calculatedTotalPrice.value
  }

  function setCatRoom(room: CatRoom) {
    selectedCatRoom.value = room
  }

  function setDates(checkIn: string, checkOut: string) {
    checkInDate.value = checkIn
    checkOutDate.value = checkOut
  }

  function setCheckInDate(date: string) {
    checkInDate.value = date
    if (checkOutDate.value && new Date(checkOutDate.value) <= new Date(date)) {
      const nextDay = new Date(date)
      nextDay.setDate(nextDay.getDate() + 1)
      checkOutDate.value = formatDate(nextDay)
    }
  }

  function setCheckOutDate(date: string) {
    checkOutDate.value = date
  }

  function toggleService(service: Service) {
    const index = selectedServices.value.findIndex((s) => s.id === service.id)
    if (index > -1) {
      selectedServices.value.splice(index, 1)
    } else {
      selectedServices.value.push(service)
    }
  }

  function addService(service: Service) {
    if (!selectedServices.value.find((s) => s.id === service.id)) {
      selectedServices.value.push(service)
    }
  }

  function removeService(serviceId: number) {
    const index = selectedServices.value.findIndex((s) => s.id === serviceId)
    if (index > -1) {
      selectedServices.value.splice(index, 1)
    }
  }

  function clearServices() {
    selectedServices.value = []
  }

  function setCatInfo(info: Partial<typeof catInfo.value>) {
    catInfo.value = { ...catInfo.value, ...info }
  }

  function setBookedDates(dates: string[]) {
    bookedDates.value = dates
  }

  function isDateBooked(date: string): boolean {
    return bookedDates.value.includes(date)
  }

  function isDateRangeAvailable(checkIn: string, checkOut: string): boolean {
    const start = new Date(checkIn)
    const end = new Date(checkOut)
    for (let d = new Date(start); d < end; d.setDate(d.getDate() + 1)) {
      if (isDateBooked(formatDate(d))) {
        return false
      }
    }
    return true
  }

  function getDisabledDate(date: Date): boolean {
    const today = new Date()
    today.setHours(0, 0, 0, 0)
    if (date < today) return true
    return isDateBooked(formatDate(date))
  }

  async function calculatePrice() {
    if (!selectedCatRoom.value || !checkInDate.value || !checkOutDate.value) return

    loading.value = true
    try {
      const res = await getBookingPrice({
        catRoomId: selectedCatRoom.value.id,
        checkInDate: formatDate(checkInDate.value),
        checkOutDate: formatDate(checkOutDate.value),
        serviceIds: selectedServices.value.map((s) => s.id)
      })
      priceInfo.value = res
      return res
    } catch (error) {
      updateLocalPrice()
      return priceInfo.value
    } finally {
      loading.value = false
    }
  }

  function resetBooking() {
    selectedCatRoom.value = null
    selectedServices.value = []
    checkInDate.value = ''
    checkOutDate.value = ''
    catInfo.value = {
      name: '',
      breed: '',
      age: 0,
      specialRequirements: ''
    }
    priceInfo.value = {
      totalPrice: 0,
      roomPrice: 0,
      servicePrice: 0,
      discount: 0
    }
    bookedDates.value = []
    loading.value = false
  }

  function getBookingData() {
    return {
      catRoomId: selectedCatRoom.value!.id,
      checkInDate: formatDate(checkInDate.value),
      checkOutDate: formatDate(checkOutDate.value),
      serviceIds: selectedServices.value.map((s) => s.id),
      catName: catInfo.value.name,
      catBreed: catInfo.value.breed,
      catAge: catInfo.value.age,
      specialRequirements: catInfo.value.specialRequirements
    }
  }

  function getPriceBreakdown() {
    return {
      roomPrice: calculatedRoomPrice.value,
      servicePrice: calculatedServicePrice.value,
      discount: priceInfo.value.discount,
      totalPrice: calculatedTotalPrice.value,
      nights: nights.value,
      roomPricePerNight: selectedCatRoom.value?.price || 0
    }
  }

  return {
    selectedCatRoom,
    selectedServices,
    checkInDate,
    checkOutDate,
    catInfo,
    priceInfo,
    loading,
    bookedDates,
    nights,
    isValid,
    isCatInfoValid,
    calculatedRoomPrice,
    calculatedServicePrice,
    calculatedTotalPrice,
    setCatRoom,
    setDates,
    setCheckInDate,
    setCheckOutDate,
    toggleService,
    addService,
    removeService,
    clearServices,
    setCatInfo,
    setBookedDates,
    isDateBooked,
    isDateRangeAvailable,
    getDisabledDate,
    calculatePrice,
    updateLocalPrice,
    resetBooking,
    getBookingData,
    getPriceBreakdown
  }
})
