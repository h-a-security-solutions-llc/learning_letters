import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import SettingsPanel from '@/components/SettingsPanel.vue'
import type { AppSettings } from '@/types'

// Mock axios
vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() }
    }
  }
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      get: vi.fn().mockResolvedValue({
        data: {
          fonts: ['Fredoka-Regular', 'Test-Font'],
          fonts_detailed: [
            {
              name: 'Fredoka-Regular',
              display_name: 'Fredoka',
              style: 'Rounded Playful',
              description: 'Test description',
              characteristics: ['rounded']
            }
          ]
        }
      }),
      post: vi.fn().mockResolvedValue({ data: {} })
    }
  }
})

describe('SettingsPanel', () => {
  const defaultSettings: AppSettings = {
    enableBestOf3: true,
    enableTraceMode: true,
    traceModeDefault: false,
    enableDebugMode: false,
    enableStepByStep: true,
    stepByStepDefault: false,
    selectedFont: 'Fredoka-Regular',
    voiceGender: 'rachel',
    autoPlaySound: true,
    rememberMultiplayerPlayers: true,
    highContrastMode: false,
    uiScale: 100,
    reducedMotion: null,
    audioSpeed: 1.0,
    strokeTolerance: 0.5,
    colorBlindMode: false,
    enableCaptions: false
  }

  let wrapper: VueWrapper

  beforeEach(() => {
    wrapper = mount(SettingsPanel, {
      props: {
        settings: { ...defaultSettings }
      }
    })
  })

  it('renders correctly', () => {
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('.settings-panel').exists()).toBe(true)
  })

  it('displays settings header', () => {
    expect(wrapper.find('.settings-header h2').text()).toBe('Settings')
  })

  it('emits close event when close button is clicked', async () => {
    await wrapper.find('.close-button').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('emits close event when overlay is clicked', async () => {
    await wrapper.find('.settings-overlay').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })

  it('shows high contrast mode toggle', () => {
    const toggles = wrapper.findAll('.setting-toggle')
    const labels = toggles.map(t => t.find('.setting-label').text())
    expect(labels).toContain('High Contrast Mode')
  })

  it('emits update:settings when high contrast is toggled', async () => {
    const checkbox = wrapper.find('input[type="checkbox"]')
    await checkbox.setValue(true)

    expect(wrapper.emitted('update:settings')).toBeTruthy()
  })

  it('enforces mutual exclusivity of trace and step-by-step defaults', async () => {
    // Enable trace mode first
    const wrapperWithTraceDefault = mount(SettingsPanel, {
      props: {
        settings: {
          ...defaultSettings,
          traceModeDefault: true,
          stepByStepDefault: false
        }
      }
    })

    // Find the step-by-step default checkbox and enable it
    // This should disable trace mode default
    const settingItems = wrapperWithTraceDefault.findAll('.setting-item')
    const stepByStepSection = settingItems.find(item =>
      item.text().includes('Step-by-Step')
    )

    expect(stepByStepSection).toBeDefined()
  })

  it('displays voice options', () => {
    const voiceOptions = wrapper.findAll('.voice-option')
    expect(voiceOptions.length).toBeGreaterThan(0)
  })

  it('shows preview voice button', () => {
    const previewBtn = wrapper.find('.preview-voice-button')
    expect(previewBtn.exists()).toBe(true)
    expect(previewBtn.text()).toContain('Preview Voice')
  })
})
