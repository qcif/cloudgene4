import { defineStore } from 'pinia'
import * as authApi from '@/api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('cg_user') || 'null'),
    token: localStorage.getItem('cg_token') || null,
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,
    isAdmin: (state) => state.user?.is_admin || false,
  },

  actions: {
    async login(username, password) {
      const { data } = await authApi.login(username, password)
      this.token = data.token
      this.user = data.user
      localStorage.setItem('cg_token', data.token)
      localStorage.setItem('cg_user', JSON.stringify(data.user))
    },

    async logout() {
      try {
        await authApi.logout()
      } finally {
        this._clear()
      }
    },

    _clear() {
      this.token = null
      this.user = null
      localStorage.removeItem('cg_token')
      localStorage.removeItem('cg_user')
    },

    updateUser(user) {
      this.user = user
      localStorage.setItem('cg_user', JSON.stringify(user))
    },
  },
})
