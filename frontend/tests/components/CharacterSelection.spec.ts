import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import CharacterSelection from '@/components/CharacterSelection.vue'

describe('CharacterSelection', () => {
  it('renders correctly', () => {
    const wrapper = mount(CharacterSelection)
    expect(wrapper.exists()).toBe(true)
  })

  it('displays category tabs', () => {
    const wrapper = mount(CharacterSelection)
    const tabs = wrapper.findAll('.category-tab')
    expect(tabs.length).toBe(3)
    expect(tabs[0].text()).toContain('A B C')
    expect(tabs[1].text()).toContain('a b c')
    expect(tabs[2].text()).toContain('1 2 3')
  })

  it('shows uppercase letters by default', () => {
    const wrapper = mount(CharacterSelection)
    const buttons = wrapper.findAll('.character-button')
    expect(buttons.length).toBe(26)
    expect(buttons[0].text()).toBe('A')
    expect(buttons[25].text()).toBe('Z')
  })

  it('switches to lowercase when tab is clicked', async () => {
    const wrapper = mount(CharacterSelection)
    const tabs = wrapper.findAll('.category-tab')

    await tabs[1].trigger('click')

    const buttons = wrapper.findAll('.character-button')
    expect(buttons.length).toBe(26)
    expect(buttons[0].text()).toBe('a')
    expect(buttons[25].text()).toBe('z')
  })

  it('switches to numbers when tab is clicked', async () => {
    const wrapper = mount(CharacterSelection)
    const tabs = wrapper.findAll('.category-tab')

    await tabs[2].trigger('click')

    const buttons = wrapper.findAll('.character-button')
    expect(buttons.length).toBe(10)
    expect(buttons[0].text()).toBe('0')
    expect(buttons[9].text()).toBe('9')
  })

  it('emits select-character event when character is clicked', async () => {
    const wrapper = mount(CharacterSelection)
    const buttons = wrapper.findAll('.character-button')

    await buttons[0].trigger('click')

    expect(wrapper.emitted('select-character')).toBeTruthy()
    expect(wrapper.emitted('select-character')![0]).toEqual(['A'])
  })

  it('applies active class to selected category tab', async () => {
    const wrapper = mount(CharacterSelection)
    const tabs = wrapper.findAll('.category-tab')

    expect(tabs[0].classes()).toContain('active')
    expect(tabs[1].classes()).not.toContain('active')

    await tabs[1].trigger('click')

    expect(tabs[0].classes()).not.toContain('active')
    expect(tabs[1].classes()).toContain('active')
  })

  it('displays instructions text', () => {
    const wrapper = mount(CharacterSelection)
    const instructions = wrapper.find('.instructions p')
    expect(instructions.text()).toContain('Tap a letter or number')
  })
})
