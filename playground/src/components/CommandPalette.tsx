import { useEffect, useMemo, useState } from 'react'
import { Command } from 'cmdk'
import { useLocation, useNavigate } from 'react-router-dom'
import { LayoutDashboard, FlaskConical, GitCommitHorizontal, Share2, Code2, Sparkles } from 'lucide-react'
import type { Namespace } from '../api'

const VIEW_ICONS = {
  train: Sparkles,
  test: FlaskConical,
  history: GitCommitHorizontal,
  graph: Share2,
  code: Code2,
}

export default function CommandPalette({ namespaces }: { namespaces: Namespace[] }) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const currentNamespace = useMemo(() => {
    const match = /^\/namespaces\/([^/]+)/.exec(location.pathname)
    return match ? decodeURIComponent(match[1]) : null
  }, [location.pathname])

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'k' && (event.metaKey || event.ctrlKey)) {
        event.preventDefault()
        setOpen((current) => !current)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [])

  function go(path: string) {
    setOpen(false)
    navigate(path)
  }

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command palette"
      className="command-palette"
    >
      <Command.Input placeholder="Jump to a namespace or view..." />
      <Command.List>
        <Command.Empty>No results found.</Command.Empty>

        <Command.Group heading="Go to">
          <Command.Item onSelect={() => go('/')}>
            <LayoutDashboard size={14} />
            Dashboard
          </Command.Item>
        </Command.Group>

        <Command.Group heading="Namespaces">
          {namespaces.map((namespace) => (
            <Command.Item
              key={namespace.name}
              onSelect={() => go(`/namespaces/${encodeURIComponent(namespace.name)}`)}
            >
              <LayoutDashboard size={14} />
              {namespace.name}
            </Command.Item>
          ))}
        </Command.Group>

        {currentNamespace && (
          <Command.Group heading={`Views in ${currentNamespace}`}>
            {(Object.keys(VIEW_ICONS) as Array<keyof typeof VIEW_ICONS>).map((view) => {
              const Icon = VIEW_ICONS[view]
              return (
                <Command.Item
                  key={view}
                  onSelect={() =>
                    go(`/namespaces/${encodeURIComponent(currentNamespace)}?left=${view}`)
                  }
                >
                  <Icon size={14} />
                  {view}
                </Command.Item>
              )
            })}
          </Command.Group>
        )}
      </Command.List>
    </Command.Dialog>
  )
}
