import { BrowserRouter, Routes, Route } from 'react-router-dom'
import NamespaceList from './pages/NamespaceList'
import NamespaceDetail from './pages/NamespaceDetail'

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
            <Route path="/namespaces/:name" element={<NamespaceDetail />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}

export default App
