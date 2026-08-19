import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom'
import NamespaceList from './pages/NamespaceList'
import NamespaceLayout from './pages/NamespaceLayout'
import NamespaceTrain from './pages/NamespaceTrain'
import NamespaceTest from './pages/NamespaceTest'
import NamespaceHistory from './pages/NamespaceHistory'
import NamespaceGraph from './pages/NamespaceGraph'

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <header className="app-header">
          <h1>TalkingDB NEL Playground</h1>
        </header>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<NamespaceList />} />
            <Route path="/namespaces/:name" element={<NamespaceLayout />}>
              <Route index element={<Navigate to="train" replace />} />
              <Route path="train" element={<NamespaceTrain />} />
              <Route path="test" element={<NamespaceTest />} />
              <Route path="history" element={<NamespaceHistory />} />
              <Route path="graph" element={<NamespaceGraph />} />
            </Route>
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
