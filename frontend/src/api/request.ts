import axios, { type AxiosInstance, type AxiosRequestConfig, type AxiosResponse, type InternalAxiosRequestConfig, type Canceler } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getToken, clearAuth } from '@/utils/auth'
import router from '@/router'

const pendingRequests = new Map<string, Canceler>()

function getRequestKey(config: AxiosRequestConfig): string {
  const { method, url, params, data } = config
  return [method, url, JSON.stringify(params), JSON.stringify(data)].join('&')
}

function addPendingRequest(config: InternalAxiosRequestConfig) {
  const key = getRequestKey(config)
  if (pendingRequests.has(key)) {
    const canceler = pendingRequests.get(key)
    canceler && canceler('重复请求已取消')
    pendingRequests.delete(key)
  }
  config.cancelToken = config.cancelToken || new axios.CancelToken((cancel) => {
    pendingRequests.set(key, cancel)
  })
}

function removePendingRequest(config: AxiosRequestConfig) {
  const key = getRequestKey(config)
  if (pendingRequests.has(key)) {
    pendingRequests.delete(key)
  }
}

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json'
  }
})

function camelToSnake(str: string): string {
  return str.replace(/[A-Z]/g, (letter) => `_${letter.toLowerCase()}`)
}

function snakeToCamel(str: string): string {
  return str.replace(/_([a-z])/g, (_, letter) => letter.toUpperCase())
}

function convertKeysToSnake(obj: any): any {
  if (obj === null || obj === undefined) return obj
  if (Array.isArray(obj)) return obj.map(convertKeysToSnake)
  if (typeof obj !== 'object') return obj

  const result: Record<string, any> = {}
  for (const key of Object.keys(obj)) {
    result[camelToSnake(key)] = convertKeysToSnake(obj[key])
  }
  return result
}

function convertKeysToCamel(obj: any): any {
  if (obj === null || obj === undefined) return obj
  if (Array.isArray(obj)) return obj.map(convertKeysToCamel)
  if (typeof obj !== 'object') return obj

  const result: Record<string, any> = {}
  for (const key of Object.keys(obj)) {
    result[snakeToCamel(key)] = convertKeysToCamel(obj[key])
  }
  return result
}

service.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    addPendingRequest(config)
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    if (config.params) {
      config.params = convertKeysToSnake(config.params)
    }
    const timestamp = Date.now()
    if (config.params) {
      config.params._t = timestamp
    } else {
      config.params = { _t: timestamp }
    }
    return config
  },
  (error) => {
    removePendingRequest(error.config || {})
    return Promise.reject(error)
  }
)

service.interceptors.response.use(
  (response: AxiosResponse) => {
    removePendingRequest(response.config)
    const res = response.data
    if (res.code !== 0) {
      if (res.code === 1002 || res.code === 2001 || res.code === 2002) {
        ElMessageBox.confirm('登录状态已过期，请重新登录', '提示', {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          clearAuth()
          router.push('/login')
        }).catch(() => {})
      } else if (res.code === 1003) {
        ElMessage.error('没有权限访问该资源')
      } else if (res.code === 1004) {
        ElMessage.error('请求的资源不存在')
      } else if (res.code >= 3000 && res.code < 4000) {
        ElMessage.error('服务器内部错误')
      } else {
        ElMessage.error(res.message || '请求失败')
      }
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return convertKeysToCamel(res.data)
  },
  (error) => {
    removePendingRequest(error.config || {})
    if (axios.isCancel(error)) {
      console.log('请求已取消:', error.message)
    } else if (error.response) {
      const status = error.response.status
      if (status === 401) {
        ElMessageBox.confirm('登录状态已过期，请重新登录', '提示', {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          clearAuth()
          router.push('/login')
        }).catch(() => {})
      } else if (status === 403) {
        ElMessage.error('没有权限访问该资源')
      } else if (status === 404) {
        ElMessage.error('请求的资源不存在')
      } else if (status >= 500) {
        ElMessage.error('服务器繁忙，请稍后重试')
      } else {
        ElMessage.error(error.response.data?.message || '请求失败')
      }
    } else if (error.request) {
      ElMessage.error('网络连接失败，请检查网络')
    } else {
      ElMessage.error(error.message || '请求失败')
    }
    return Promise.reject(error)
  }
)

export function request<T>(config: AxiosRequestConfig): Promise<T> {
  return service.request<T, T>(config)
}

export function get<T>(url: string, params?: object, config?: AxiosRequestConfig): Promise<T> {
  return request<T>({ method: 'GET', url, params, ...config })
}

export function post<T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
  return request<T>({ method: 'POST', url, data, ...config })
}

export function put<T>(url: string, data?: object, config?: AxiosRequestConfig): Promise<T> {
  return request<T>({ method: 'PUT', url, data, ...config })
}

export function del<T>(url: string, params?: object, config?: AxiosRequestConfig): Promise<T> {
  return request<T>({ method: 'DELETE', url, params, ...config })
}

export default service
