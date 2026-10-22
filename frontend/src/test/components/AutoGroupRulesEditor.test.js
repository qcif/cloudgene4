import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

vi.mock('@/api/admin', () => ({
  getAutoGroups: vi.fn(),
  updateAutoGroups: vi.fn(),
  testAutoGroups: vi.fn(),
}))
vi.mock('vue-router', () => ({ onBeforeRouteLeave: vi.fn() }))
vi.mock('@/api/users', () => ({
  listGroups: vi.fn(),
  createGroup: vi.fn(),
  deleteGroup: vi.fn(),
}))

import { getAutoGroups, updateAutoGroups, testAutoGroups } from '@/api/admin'
import { listGroups } from '@/api/users'
import AutoGroupRulesEditor from '@/components/admin/AutoGroupRulesEditor.vue'
import AdminGroupsView from '@/views/admin/AdminGroupsView.vue'

const RULES = [
  { pattern: '.*@unimelb\\.edu\\.au', groups: ['unimelb'] },
  { pattern: '.*@example\\.org', groups: ['example', 'trial'] },
]
const GROUPS = [
  { id: 1, name: 'admin', member_count: 1 },
  { id: 2, name: 'unimelb', member_count: 3 },
  { id: 3, name: 'plain', member_count: 0 },
]

const mountEditor = (props = {}) =>
  mount(AutoGroupRulesEditor, {
    props: { rules: RULES.map((r) => ({ ...r, groups: [...r.groups] })), existingGroups: GROUPS, ...props },
  })

const apiError = (fields, message = 'bad') => ({
  response: { data: { error: { code: 'invalid', message, fields } } },
})

describe('AutoGroupRulesEditor', () => {
  beforeEach(() => vi.clearAllMocks())

  it('renders the rules and warns only when activation is off', () => {
    let wrapper = mountEditor()
    expect(wrapper.findAll('[data-testid="auto-rule-row"]')).toHaveLength(2)
    expect(wrapper.findAll('[data-testid="auto-rule-pattern"]')[1].element.value).toBe('.*@example\\.org')
    expect(wrapper.find('[data-testid="auto-rules-activation-off"]').exists()).toBe(false)
    wrapper = mountEditor({ requireActivation: false })
    expect(wrapper.find('[data-testid="auto-rules-activation-off"]').exists()).toBe(true)
  })

  it('adds, reorders and removes rules', async () => {
    const wrapper = mountEditor()
    await wrapper.get('[data-testid="auto-rule-add"]').trigger('click')
    expect(wrapper.findAll('[data-testid="auto-rule-row"]')).toHaveLength(3)
    expect(wrapper.text()).toContain('This rule never matches')
    await wrapper.findAll('[data-testid="auto-rule-down"]')[0].trigger('click')
    expect(wrapper.findAll('[data-testid="auto-rule-pattern"]')[0].element.value).toBe('.*@example\\.org')
    await wrapper.findAll('[data-testid="auto-rule-remove"]')[2].trigger('click')
    expect(wrapper.findAll('[data-testid="auto-rule-row"]')).toHaveLength(2)
  })

  it('adds existing and new group names, and rejects admin and invalid names', async () => {
    const wrapper = mountEditor()
    const input = () => wrapper.findAll('[data-testid="auto-rule-group-input"]')[0]
    const add = () => wrapper.findAll('[data-testid="auto-rule-group-add"]')[0].trigger('click')

    await input().setValue('plain')
    await add()
    await input().setValue('brand-new')
    await add()
    const row = wrapper.findAll('[data-testid="auto-rule-row"]')[0]
    expect(row.text()).toContain('plain')
    expect(row.findAll('[data-testid="auto-rule-group-new"]')).toHaveLength(1)

    await input().setValue('Admin')
    await add()
    expect(row.get('[data-testid="auto-rule-groups-error"]').text()).toContain('admin')
    await input().setValue('no good!')
    await add()
    expect(row.get('[data-testid="auto-rule-groups-error"]').text()).toContain('Group names')
    expect(row.findAll('[data-testid="auto-rule-group"]')).toHaveLength(3)
    expect(wrapper.html()).not.toContain('<option value="admin"')
    expect(updateAutoGroups).not.toHaveBeenCalled()
  })

  it('saves the full list and shows server errors under the right row', async () => {
    updateAutoGroups.mockRejectedValueOnce(apiError({ 'auto_groups[1].pattern': ['Not a valid regular expression'] }, 'auto_groups[1].pattern: nope'))
    const wrapper = mountEditor()
    await wrapper.get('[data-testid="auto-rules-save"]').trigger('click')
    await flushPromises()
    expect(updateAutoGroups).toHaveBeenCalledWith(RULES)
    const rows = wrapper.findAll('[data-testid="auto-rule-row"]')
    expect(rows[0].get('[data-testid="auto-rule-pattern-error"]').text()).toBe('')
    expect(rows[1].get('[data-testid="auto-rule-pattern-error"]').text()).toContain('Not a valid')
    expect(wrapper.get('[data-testid="auto-rules-error"]').text()).toContain('nope')

    updateAutoGroups.mockResolvedValueOnce({ data: { auto_groups: RULES, require_activation: true } })
    await wrapper.get('[data-testid="auto-rules-save"]').trigger('click')
    await flushPromises()
    expect(wrapper.get('[data-testid="auto-rules-success"]').text()).toBe('Rules saved.')
    expect(wrapper.find('[data-testid="auto-rules-error"]').exists()).toBe(false)
    expect(wrapper.emitted('saved')).toHaveLength(1)
  })

  it('disables Save while the request runs', async () => {
    let resolve
    updateAutoGroups.mockReturnValueOnce(new Promise((r) => { resolve = r }))
    const wrapper = mountEditor()
    await wrapper.get('[data-testid="auto-rules-save"]').trigger('click')
    expect(wrapper.get('[data-testid="auto-rules-save"]').attributes('disabled')).toBeDefined()
    resolve({ data: { auto_groups: RULES, require_activation: true } })
    await flushPromises()
    expect(wrapper.get('[data-testid="auto-rules-save"]').attributes('disabled')).toBeUndefined()
  })

  it('tests an address with the unsaved rules, highlights matches and clears on edit', async () => {
    testAutoGroups.mockResolvedValue({ data: { email: 'a@example.org', matched_rules: [1], groups: ['example', 'trial'] } })
    const wrapper = mountEditor()
    await wrapper.findAll('[data-testid="auto-rule-pattern"]')[0].setValue('.*@changed')
    await wrapper.get('[data-testid="auto-test-email"]').setValue('a@example.org')
    await wrapper.get('[data-testid="auto-test-form"]').trigger('submit')
    await flushPromises()

    const sent = testAutoGroups.mock.calls[0]
    expect(sent[0]).toBe('a@example.org')
    expect(sent[1][0].pattern).toBe('.*@changed')
    expect(wrapper.get('[data-testid="auto-test-result"]').text()).toContain('rule 2')
    expect(wrapper.get('[data-testid="auto-test-result"]').text()).toContain('example, trial')
    const rows = wrapper.findAll('[data-testid="auto-rule-row"]')
    expect(rows.map((r) => r.attributes('data-matched'))).toEqual(['false', 'true'])

    await wrapper.findAll('[data-testid="auto-rule-pattern"]')[1].setValue('x')
    expect(wrapper.find('[data-testid="auto-test-result"]').exists()).toBe(false)
    expect(wrapper.findAll('[data-testid="auto-rule-row"]').every((r) => r.attributes('data-matched') === 'false')).toBe(true)
  })

  it('omits rules from the test when there are no unsaved changes, and shows no-match', async () => {
    testAutoGroups.mockResolvedValue({ data: { email: 'a@b.org', matched_rules: [], groups: [] } })
    const wrapper = mountEditor()
    await wrapper.get('[data-testid="auto-test-email"]').setValue('a@b.org')
    await wrapper.get('[data-testid="auto-test-form"]').trigger('submit')
    await flushPromises()
    expect(testAutoGroups).toHaveBeenCalledWith('a@b.org', undefined)
    expect(wrapper.get('[data-testid="auto-test-result"]').text()).toBe('No rule matches this address.')
  })

  it('shows server errors from the test under the field and the row', async () => {
    const wrapper = mountEditor()
    await wrapper.get('[data-testid="auto-test-email"]').setValue('nope')
    await wrapper.get('[data-testid="auto-test-form"]').trigger('submit')
    expect(testAutoGroups).not.toHaveBeenCalled()
    expect(wrapper.get('[data-testid="auto-test-error"]').text()).not.toBe('')

    testAutoGroups.mockRejectedValueOnce(apiError({ 'auto_groups[0].pattern': ['Not a valid regular expression'] }))
    await wrapper.get('[data-testid="auto-test-email"]').setValue('a@b.org')
    await wrapper.get('[data-testid="auto-test-form"]').trigger('submit')
    await flushPromises()
    expect(wrapper.findAll('[data-testid="auto-rule-pattern-error"]')[0].text()).toContain('Not a valid')
  })

  it('renders patterns, group names and results as text', async () => {
    const evil = '<img src=x onerror=alert(1)>'
    const wrapper = mountEditor({ rules: [{ pattern: evil, groups: [evil.replace(/[<>]/g, '')] }] })
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.get('[data-testid="auto-rule-pattern"]').element.value).toBe(evil)
    testAutoGroups.mockResolvedValue({ data: { email: 'a@b.org', matched_rules: [0], groups: [evil] } })
    await wrapper.get('[data-testid="auto-test-email"]').setValue('a@b.org')
    await wrapper.get('[data-testid="auto-test-form"]').trigger('submit')
    await flushPromises()
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.get('[data-testid="auto-test-result"]').text()).toContain(evil)
  })
})

describe('AdminGroupsView automatic membership', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listGroups.mockResolvedValue({ data: GROUPS })
    getAutoGroups.mockResolvedValue({ data: { auto_groups: RULES, require_activation: true } })
  })

  const mountModal = async () => {
    const wrapper = mount(AdminGroupsView, { global: { stubs: { AdminLayout: { template: '<div><slot /></div>' } } } })
    await flushPromises()
    return wrapper
  }

  it('marks groups named by a rule and warns when deleting one', async () => {
    const wrapper = await mountModal()
    const rows = wrapper.findAll('[data-testid="group-row"]')
    const badge = (name) => rows.find((r) => r.attributes('data-group') === name).find('[data-testid="group-auto-badge"]')
    expect(badge('unimelb').exists()).toBe(true)
    expect(badge('plain').exists()).toBe(false)

    await rows.find((r) => r.attributes('data-group') === 'unimelb').get('[data-testid="group-delete"]').trigger('click')
    expect(wrapper.get('[data-testid="group-delete-dialog"]').text()).toContain('Automatic membership rules name this group')
    await wrapper.get('[data-testid="group-delete-cancel"]').trigger('click')
    await rows.find((r) => r.attributes('data-group') === 'plain').get('[data-testid="group-delete"]').trigger('click')
    expect(wrapper.get('[data-testid="group-delete-dialog"]').text()).not.toContain('Automatic membership rules')
  })

  it('shows the member count as the button that opens the members', async () => {
    const wrapper = await mountModal()
    const row = wrapper.findAll('[data-testid="group-row"]').find((r) => r.attributes('data-group') === 'unimelb')
    const button = row.get('button[data-testid="group-members"]')
    expect(button.attributes('title')).toBe('View')
    expect(button.get('[data-testid="group-member-count"]').text()).toBe('3')
    expect(row.findAll('[data-testid="group-members"]')).toHaveLength(1)
  })

  it('shows the load error and asks before discarding unsaved edits', async () => {
    getAutoGroups.mockRejectedValueOnce({})
    let wrapper = await mountModal()
    await wrapper.get('[data-testid="group-tab-auto"]').trigger('click')
    expect(wrapper.text()).toContain('Could not load automatic membership rules.')

    wrapper = await mountModal()
    await wrapper.get('[data-testid="group-tab-auto"]').trigger('click')
    await wrapper.get('[data-testid="auto-rule-add"]').trigger('click')
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
    await wrapper.get('[data-testid="group-tab-groups"]').trigger('click')
    expect(confirm).toHaveBeenCalled()
    expect(wrapper.find('[data-testid="auto-rules-editor"]').exists()).toBe(true)
    confirm.mockReturnValue(true)
    await wrapper.get('[data-testid="group-tab-groups"]').trigger('click')
    expect(wrapper.find('[data-testid="auto-rules-editor"]').exists()).toBe(false)
    confirm.mockRestore()
  })
})
