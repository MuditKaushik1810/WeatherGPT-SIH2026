import { render, screen, fireEvent } from '@testing-library/react'
import Settings from './Settings'
import { resetLanguageForTests, getLanguage } from '../i18n'

beforeEach(() => {
  localStorage.clear()
  resetLanguageForTests()
})

it('renders the language, location and farmer sections', () => {
  render(<Settings />)
  expect(screen.getByRole('heading', { name: 'Language' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Location' })).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Farmer preferences' })).toBeInTheDocument()
})

it('saves a default location and lists it under saved places', () => {
  render(<Settings />)
  fireEvent.change(screen.getByLabelText('Default location'), { target: { value: 'Jaipur' } })
  fireEvent.click(screen.getAllByRole('button', { name: 'Save' })[0])

  expect(localStorage.getItem('weathergpt.defaultLocation')).toBe('Jaipur')
  // The default is mirrored into the saved list, with a Remove control.
  expect(screen.getByRole('button', { name: 'Remove Jaipur' })).toBeInTheDocument()
})

it('adds and removes a saved place', () => {
  render(<Settings />)
  fireEvent.change(screen.getByLabelText('Add a place'), { target: { value: 'Mumbai' } })
  fireEvent.click(screen.getByRole('button', { name: 'Add' }))
  expect(screen.getByText('Mumbai')).toBeInTheDocument()

  fireEvent.click(screen.getByRole('button', { name: 'Remove Mumbai' }))
  expect(screen.queryByText('Mumbai')).not.toBeInTheDocument()
})

it('makes a saved place the active location when shown', () => {
  render(<Settings />)
  fireEvent.change(screen.getByLabelText('Add a place'), { target: { value: 'Pune' } })
  fireEvent.click(screen.getByRole('button', { name: 'Add' }))

  fireEvent.click(screen.getByRole('button', { name: 'Show' }))
  expect(localStorage.getItem('weathergpt.location')).toBe('Pune')
})

it('persists farmer preferences', () => {
  render(<Settings />)
  fireEvent.change(screen.getByLabelText('Crop'), { target: { value: 'Wheat' } })
  fireEvent.change(screen.getByLabelText('Farm location'), { target: { value: 'Karnal' } })
  // The farmer Save is the last Save button on the screen.
  const saves = screen.getAllByRole('button', { name: 'Save' })
  fireEvent.click(saves[saves.length - 1])

  expect(localStorage.getItem('weathergpt.farmer.crop')).toBe('Wheat')
  expect(localStorage.getItem('weathergpt.farmer.location')).toBe('Karnal')
})

it('changes the app language from the selector', () => {
  render(<Settings />)
  fireEvent.change(screen.getByLabelText('Language'), { target: { value: 'hi' } })
  expect(getLanguage()).toBe('hi')
  expect(localStorage.getItem('weathergpt.language')).toBe('hi')
})
