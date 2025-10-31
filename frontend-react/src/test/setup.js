import { expect, afterEach, vi, beforeEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom'
import React from 'react'

// React를 전역으로 설정
global.React = React

// 각 테스트 후 정리
afterEach(() => {
  cleanup()
})

// 전역 mock 설정
global.matchMedia = global.matchMedia || function() {
  return {
    matches: false,
    addListener: vi.fn(),
    removeListener: vi.fn(),
  }
}

// localStorage mock
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
}
global.localStorage = localStorageMock

// fetch mock
global.fetch = vi.fn()
