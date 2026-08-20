import { describe, expect, it } from 'vitest'
import { isViewKey, getPaneView, normalizeViewKey, otherDefaultView, VIEW_KEYS } from './paneViews'

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

describe('normalizeViewKey', () => {
  it('passes known view keys through unchanged', () => {
    expect(normalizeViewKey('train')).toBe('train')
  })

  it('maps the legacy "graph" key to the merged "inspect" view', () => {
    expect(normalizeViewKey('graph')).toBe('inspect')
  })

  it('returns null for anything else', () => {
    expect(normalizeViewKey('nope')).toBeNull()
    expect(normalizeViewKey(null)).toBeNull()
    expect(normalizeViewKey(undefined)).toBeNull()
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
    expect(otherDefaultView('inspect')).toBe('train')
  })
})
