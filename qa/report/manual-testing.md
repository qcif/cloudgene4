# Manual tests by a human

**Bugs found:**

1. When an account is created with the same email as another account, it results in a server error due to the database-level unique constraint not being handled.

1. The default workflow "run page" (/run/hello-cloudgene) does not show any of the configured inputs in the UI.

1. Frontend /admin/users page is broken with:
    - Uncaught (in promise) TypeError: server.navbarItems.filter is not a function
    - Uncaught (in promise) TypeError: Cannot read properties of null (reading 'id')
        at AdminUsersView.vue:120:52
        at renderList (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:3868:13)
        at AdminUsersView.vue:131:25
        at renderList (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:3854:59)
        at AdminUsersView.vue:142:20
        at renderFnWithContext (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:2254:10)
        at renderSlot (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:3900:52)
        at Proxy._sfc_render (AdminLayout.vue:9:7)

1. Frontend /admin/settings/templates is broken with:
    - TemplateEditorView.vue:48 Uncaught (in promise) TypeError: Cannot read properties of null (reading 'id')
        at TemplateEditorView.vue:48:49
        at renderList (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:3868:13)
        at TemplateEditorView.vue:68:13
        at renderFnWithContext (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:2254:10)
        at renderSlot (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:3900:52)
        at Proxy._sfc_render (AdminLayout.vue:9:7)

1. Frontend admin panel "Back to site" link doesn't work
    - Raises: Uncaught (in promise) TypeError: server.navbarItems.filter is not a function
        at ComputedRefImpl.fn (AppNavbar.vue:12:22)
        at refreshComputed (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:542:26)
        at get value (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:1529:3)
        at unref (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:1374:44)
        at Object.get (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:1380:63)
        at Proxy._sfc_render (AppNavbar.vue:48:28)
    - Routes in general seem to be broken, "Back" button in browser changes the route but renders a blank page with console errors like:
        vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:5807 Uncaught (in promise) TypeError: Cannot destructure property 'type' of 'vnode' as it is null.
            at unmount (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:5807:11)
            at unmountComponent (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:5885:4)
            at unmount (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:5823:22)
            at unmountChildren (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:5894:49)
            at unmount (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:5831:116)
            at patch (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:5260:4)
            at ReactiveEffect.componentUpdateFn [as fn] (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:5603:5)
            at ReactiveEffect.run (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:419:16)
            at ReactiveEffect.runIfDirty (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:446:27)
            at callWithErrorHandling (vue.runtime.esm-bundler-KoyTRBhz.js?v=e2b0c377:1883:31)
