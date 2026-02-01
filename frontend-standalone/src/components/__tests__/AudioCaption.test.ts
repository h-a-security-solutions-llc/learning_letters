import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AudioCaption from '../AudioCaption.vue'

describe('AudioCaption', () => {
  describe('rendering', () => {
    it('does not render when isVisible is false', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital A',
          isVisible: false
        }
      })

      expect(wrapper.find('.audio-caption-toast').exists()).toBe(false)
    })

    it('does not render when caption is null', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: null,
          isVisible: true
        }
      })

      expect(wrapper.find('.audio-caption-toast').exists()).toBe(false)
    })

    it('renders when both caption and isVisible are truthy', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital A',
          isVisible: true
        }
      })

      expect(wrapper.find('.audio-caption-toast').exists()).toBe(true)
    })

    it('displays the caption text', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital A',
          isVisible: true
        }
      })

      expect(wrapper.find('.caption-character').text()).toBe('Capital A')
    })

    it('displays the speaker icon', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital A',
          isVisible: true
        }
      })

      expect(wrapper.find('.caption-icon').text()).toContain('🔊')
    })
  })

  describe('accessibility', () => {
    it('has role="status" for screen readers', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital A',
          isVisible: true
        }
      })

      expect(wrapper.find('[role="status"]').exists()).toBe(true)
    })

    it('has aria-live="polite" for screen readers', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital A',
          isVisible: true
        }
      })

      expect(wrapper.find('[aria-live="polite"]').exists()).toBe(true)
    })
  })

  describe('props', () => {
    it('accepts caption prop', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Number 5',
          isVisible: true
        }
      })

      expect(wrapper.props('caption')).toBe('Number 5')
    })

    it('accepts isVisible prop', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Lowercase a',
          isVisible: true
        }
      })

      expect(wrapper.props('isVisible')).toBe(true)
    })

    it('has default caption of null', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          isVisible: true
        }
      })

      expect(wrapper.props('caption')).toBeNull()
    })

    it('has default isVisible of false', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Test'
        }
      })

      expect(wrapper.props('isVisible')).toBe(false)
    })
  })

  describe('different caption types', () => {
    it('displays uppercase letter captions', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital B',
          isVisible: true
        }
      })

      expect(wrapper.find('.caption-character').text()).toBe('Capital B')
    })

    it('displays lowercase letter captions', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Lowercase b',
          isVisible: true
        }
      })

      expect(wrapper.find('.caption-character').text()).toBe('Lowercase b')
    })

    it('displays number captions', () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Number 7',
          isVisible: true
        }
      })

      expect(wrapper.find('.caption-character').text()).toBe('Number 7')
    })
  })

  describe('visibility transitions', () => {
    it('shows caption when visibility changes to true', async () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital A',
          isVisible: false
        }
      })

      expect(wrapper.find('.audio-caption-toast').exists()).toBe(false)

      await wrapper.setProps({ isVisible: true })

      expect(wrapper.find('.audio-caption-toast').exists()).toBe(true)
    })

    it('hides caption when visibility changes to false', async () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital A',
          isVisible: true
        }
      })

      expect(wrapper.find('.audio-caption-toast').exists()).toBe(true)

      await wrapper.setProps({ isVisible: false })

      expect(wrapper.find('.audio-caption-toast').exists()).toBe(false)
    })

    it('updates caption text when prop changes', async () => {
      const wrapper = mount(AudioCaption, {
        props: {
          caption: 'Capital A',
          isVisible: true
        }
      })

      expect(wrapper.find('.caption-character').text()).toBe('Capital A')

      await wrapper.setProps({ caption: 'Capital B' })

      expect(wrapper.find('.caption-character').text()).toBe('Capital B')
    })
  })
})
