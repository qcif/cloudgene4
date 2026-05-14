import { defineStore } from 'pinia'
import { getNavbarItems, getTemplates } from '@/api/admin'

export const useServerStore = defineStore('server', {
  state: () => ({
    navbarItems: [],
    templates: {},
    loaded: false,
  }),

  actions: {
    async load() {
      if (this.loaded) return
      try {
        const [navRes, tmplRes] = await Promise.all([
          getNavbarItems(),
          getTemplates(),
        ])
        this.navbarItems = navRes.data.results || []
        const map = {}
        const templates = tmplRes.data.results || []
        for (const t of templates) {
          map[t.name] = t.content
        }
        this.templates = map
        this.loaded = true
      } catch (error) {
        console.warn('Failed to load server data:', error)
        // Ensure navbarItems is always an array
        this.navbarItems = this.navbarItems || []
      }
    },
  },
})
