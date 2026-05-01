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
        this.navbarItems = navRes.data
        const map = {}
        for (const t of tmplRes.data) {
          map[t.name] = t.content
        }
        this.templates = map
        this.loaded = true
      } catch {
        // server store is best-effort; non-fatal
      }
    },
  },
})
