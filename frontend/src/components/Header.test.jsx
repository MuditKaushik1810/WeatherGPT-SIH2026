import { render, screen, fireEvent } from '@testing-library/react'
import Header from './Header'
import { getPersona } from '../lib/preferences'
import { resetLanguageForTests } from '../i18n'

beforeEach(() => {
  localStorage.clear()
  resetLanguageForTests()
  window.location.hash = ''
})

it('opens a menu from the hamburger with the persona switch and Settings', () => {
  render(<Header location="Delhi" />)
  // Menu is closed initially.
  expect(screen.queryByRole('menuitem', { name: /Farmer Mode/i })).not.toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Menu' }))

  expect(screen.getByRole('menuitem', { name: /Switch to Farmer Mode/i })).toBeInTheDocument()
  expect(screen.getByRole('menuitem', { name: /Settings/i })).toBeInTheDocument()
})

it('entering Farmer Mode persists the persona and lands on Crop Watch', () => {
  render(<Header location="Delhi" />)
  fireEvent.click(screen.getByRole('button', { name: 'Menu' }))
  fireEvent.click(screen.getByRole('menuitem', { name: /Switch to Farmer Mode/i }))

  expect(getPersona()).toBe('farmer')
  expect(window.location.hash).toBe('#farmer/watch')
})

it('Settings navigates to the settings screen', () => {
  render(<Header location="Delhi" />)
  fireEvent.click(screen.getByRole('button', { name: 'Menu' }))
  fireEvent.click(screen.getByRole('menuitem', { name: /Settings/i }))

  expect(window.location.hash).toBe('#settings')
})
