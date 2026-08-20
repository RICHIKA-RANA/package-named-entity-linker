import { BrowserRouter, Navigate, Routes, Route, useParams } from 'react-router-dom'
import AppShell from './components/AppShell'
import ToastProvider from './components/ToastProvider'
import Dashboard from './pages/Dashboard'
import NamespaceWorkspace from './pages/NamespaceWorkspace'
import { isViewKey } from './pages/paneViews'

function LegacyViewRedirect() {
  const { name, view } = useParams<{ name: string; view: string }>()

  if (!name) return <Navigate to="/" replace />

  const left = isViewKey(view) ? view : 'train'

  return <Navigate to={`/namespaces/${encodeURIComponent(name)}?left=${left}`} replace />
}

function App() {
  return (
    <BrowserRouter>
      <ToastProvider>
        <AppShell>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/namespaces/:name" element={<NamespaceWorkspace />} />
            <Route path="/namespaces/:name/:view" element={<LegacyViewRedirect />} />
          </Routes>
        </AppShell>
      </ToastProvider>
    </BrowserRouter>
  )
}

export default App
