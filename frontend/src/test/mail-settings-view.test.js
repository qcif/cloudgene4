import { describe, it, expect, vi, beforeEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'

vi.mock('@/api/admin', () => ({
  getMailSettings: vi.fn(),
  updateMailSettings: vi.fn(),
  sendTestMail: vi.fn(),
}))

import { getMailSettings, updateMailSettings } from '@/api/admin'
import MailSettingsView from '@/views/admin/settings/MailSettingsView.vue'

const SETTINGS = {
  backend: 'smtp',
  file_path: 'mail',
  host: 'smtp.qfab.org',
  port: 587,
  user: 'qfab_smtp',
  use_tls: true,
  use_ssl: false,
  from_email: 'qfab_smtp@qfab.org',
  from_name: '',
  password_set: true,
}

async function mountView(settings = SETTINGS) {
  getMailSettings.mockResolvedValue({ data: { ...settings } })
  const wrapper = mount(MailSettingsView, {
    global: { stubs: { AdminLayout: { template: '<div><slot /></div>' } } },
  })
  await flushPromises()
  return wrapper
}

describe('MailSettingsView sender name', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows the stored sender name', async () => {
    const wrapper = await mountView({ ...SETTINGS, from_name: 'Cloudgene' })
    expect(wrapper.get('[data-testid="mail-from-name"]').element.value).toBe('Cloudgene')
  })

  it('sends the edited sender name on save', async () => {
    updateMailSettings.mockImplementation(async (data) => ({ data: { ...data, password_set: true } }))
    const wrapper = await mountView()

    await wrapper.get('[data-testid="mail-from-name"]').setValue('Cloudgene')
    await wrapper.get('[data-testid="mail-form"]').trigger('submit')
    await flushPromises()

    expect(updateMailSettings).toHaveBeenCalledTimes(1)
    const sent = updateMailSettings.mock.calls[0][0]
    expect(sent.from_name).toBe('Cloudgene')
    expect(sent.from_email).toBe('qfab_smtp@qfab.org')
    expect(sent).not.toHaveProperty('password_set')
    expect(wrapper.find('[data-testid="mail-success"]').exists()).toBe(true)
  })

  it('shows the server error on the sender name field', async () => {
    updateMailSettings.mockRejectedValue({
      response: {
        status: 400,
        data: { error: { code: 'invalid', message: 'Invalid', fields: { from_name: ['Must be a single line.'] } } },
      },
    })
    const wrapper = await mountView()

    await wrapper.get('[data-testid="mail-form"]').trigger('submit')
    await flushPromises()

    const input = wrapper.get('[data-testid="mail-from-name"]')
    expect(input.classes()).toContain('is-invalid')
    expect(input.element.parentElement.textContent).toContain('Must be a single line.')
  })

  it('shows the sender name field for non-SMTP backends too', async () => {
    const wrapper = await mountView({ ...SETTINGS, backend: 'file' })
    expect(wrapper.find('[data-testid="mail-from-name"]').exists()).toBe(true)
  })
})
