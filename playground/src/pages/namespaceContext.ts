import { createContext, useContext } from 'react'

export interface NamespaceContext {
  namespace: string
}

const NamespaceCtx = createContext<NamespaceContext | null>(null)

export const NamespaceProvider = NamespaceCtx.Provider

export function useNamespaceContext(): NamespaceContext {
  const context = useContext(NamespaceCtx)

  if (!context) {
    throw new Error('useNamespaceContext must be used within a NamespaceProvider')
  }

  return context
}
