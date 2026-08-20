import { describe, expect, it } from 'vitest'
import { isViewKey, getPaneView, otherDefaultView, VIEW_KEYS } from './paneViews'

describe('isViewKey', () => {
  it('accepts every known view key', () => {
    VIEW_KEYS.forEach((key) => expect(isViewKey(key)).toBe(true))
  })

  it('rejects unknown strings, null, and undefined', () => {
    expect(isViewKey('nope')).toBe(false)
    expect(isViewKey(null)).toBe(false)
    expect(isViewKey(undefined)).toBe(false)
  })
})

describe('getPaneView', () => {
  it('returns the view descriptor for a known key', () => {
    expect(getPaneView('train').label).toBe('Train')
  })

  it('throws for an unknown key', () => {
    // @ts-expect-error - deliberately passing an invalid key
    expect(() => getPaneView('nope')).toThrow()
  })
})

describe('otherDefaultView', () => {
  it('returns the right default when given the left default', () => {
    expect(otherDefaultView('train')).toBe('test')
  })

  it('returns the left default for any other view', () => {
    expect(otherDefaultView('test')).toBe('train')
    expect(otherDefaultView('graph')).toBe('train')
  })
})
