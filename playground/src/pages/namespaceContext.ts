import { useOutletContext } from 'react-router-dom'

export interface NamespaceContext {
  namespace: string
}

export function useNamespaceContext() {
  return useOutletContext<NamespaceContext>()
}
