export interface PaymentMethod {
  id: string
  name: string
  icon: string
  description: string
}

export const paymentMethods: PaymentMethod[] = [
  {
    id: 'wechat',
    name: '微信支付',
    icon: 'wechat',
    description: '使用微信扫码支付'
  },
  {
    id: 'alipay',
    name: '支付宝',
    icon: 'alipay',
    description: '使用支付宝扫码支付'
  },
  {
    id: 'card',
    name: '银行卡',
    icon: 'credit-card',
    description: '使用银行卡支付'
  },
  {
    id: 'balance',
    name: '余额支付',
    icon: 'wallet',
    description: '使用账户余额支付'
  }
]

export function generateOrderNo(): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  const random = Math.floor(Math.random() * 10000).toString().padStart(4, '0')
  return `${year}${month}${day}${hours}${minutes}${seconds}${random}`
}

export function formatPrice(price: number): string {
  return `¥${price.toFixed(2)}`
}

export function calculateDiscount(originalPrice: number, discount: number): number {
  return originalPrice * (1 - discount / 100)
}

export function getPaymentMethodName(id: string): string {
  const method = paymentMethods.find((m) => m.id === id)
  return method?.name || '未知支付方式'
}

export const orderStatusMap: Record<string, { label: string; type: string }> = {
  pending: { label: '待确认', type: 'warning' },
  confirmed: { label: '已确认', type: 'primary' },
  paid: { label: '已支付', type: 'success' },
  cancelled: { label: '已取消', type: 'info' },
  completed: { label: '已完成', type: 'success' }
}

export const paymentStatusMap: Record<string, { label: string; type: string }> = {
  unpaid: { label: '未支付', type: 'danger' },
  paid: { label: '已支付', type: 'success' },
  refunded: { label: '已退款', type: 'info' }
}

export function getOrderStatusLabel(status: string): string {
  return orderStatusMap[status]?.label || status
}

export function getPaymentStatusLabel(status: string): string {
  return paymentStatusMap[status]?.label || status
}
