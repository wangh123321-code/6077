const TOKEN_KEY = 'cat_hotel_token'
const USER_KEY = 'cat_hotel_user'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}

export function getUser<T>(): T | null {
  const userStr = localStorage.getItem(USER_KEY)
  return userStr ? (JSON.parse(userStr) as T) : null
}

export function setUser<T>(user: T): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function removeUser(): void {
  localStorage.removeItem(USER_KEY)
}

export function clearAuth(): void {
  removeToken()
  removeUser()
}
