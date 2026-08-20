import { useEffect, useMemo, useState, type ReactNode } from 'react'
import { NavLink, useLocation, useSearchParams } from 'react-router-dom'
import { AnimatePresence, motion } from 'motion/react'
import { LayoutDashboard, Menu, X, Command as CommandIcon } from 'lucide-react'
import { listNamespaces, type Namespace } from '../api'
import { PANE_VIEWS, DEFAULT_LEFT_VIEW, normalizeViewKey } from '../pages/paneViews'
import CommandPalette from './CommandPalette'
import NamespaceSwitcher from './NamespaceSwitcher'
import { useMediaQuery } from '../hooks/useMediaQuery'

export default function AppShell({ children }: { children: ReactNode }) {
  const [namespaces, setNamespaces] = useState<Namespace[]>([])
  const [drawerOpen, setDrawerOpen] = useState(false)
  const isDesktop = useMediaQuery('(min-width: 1024px)')
  const location = useLocation()
  const [searchParams] = useSearchParams()

  const currentNamespace = useMemo(() => {
    const match = /^\/namespaces\/([^/]+)/.exec(location.pathname)
    return match ? decodeURIComponent(match[1]) : null
  }, [location.pathname])

  const activeView = normalizeViewKey(searchParams.get('left')) ?? DEFAULT_LEFT_VIEW

  useEffect(() => {
    listNamespaces()
      .then(setNamespaces)
      .catch(() => {
        /* sidebar list is best-effort - errors surface on the Dashboard itself */
      })
  }, [location.pathname])

  const sidebarContent = (
    <>
      <div className="sidebar-header">
        <NavLink to="/" end className="sidebar-brand">
          <LayoutDashboard size={18} />
          TalkingDB NEL
        </NavLink>
      </div>

      {currentNamespace ? (
        <>
          <NamespaceSwitcher namespaces={namespaces} current={currentNamespace} />

          <div className="sidebar-section-label">Namespace</div>
          <nav className="sidebar-nav">
            {PANE_VIEWS.map((view) => (
              <NavLink
                key={view.key}
                to={`/namespaces/${encodeURIComponent(currentNamespace)}?left=${view.key}`}
                // Every section link shares the same pathname (only `?left=`
                // differs), so NavLink's own pathname-only isActive would mark
                // all of them active at once - use a function className to
                // fully own the active state from our own `left` comparison.
                className={() => (view.key === activeView ? 'sidebar-link active' : 'sidebar-link')}
              >
                <view.icon size={16} />
                {view.label}
              </NavLink>
            ))}
          </nav>
        </>
      ) : (
        <nav className="sidebar-nav">
          <NavLink to="/" end className="sidebar-link">
            <LayoutDashboard size={16} />
            Dashboard
          </NavLink>
        </nav>
      )}

      <button
        type="button"
        className="sidebar-cmdk-hint"
        onClick={() =>
          document.dispatchEvent(
            new KeyboardEvent('keydown', { key: 'k', metaKey: true }),
          )
        }
      >
        <CommandIcon size={14} />
        <span>Quick jump</span>
        <kbd>&#8984;K</kbd>
      </button>
    </>
  )

  return (
    <div className="app-shell">
      {isDesktop ? (
        <aside className="sidebar">{sidebarContent}</aside>
      ) : (
        <>
          <button
            type="button"
            className="mobile-menu-button"
            onClick={() => setDrawerOpen(true)}
            aria-label="Open menu"
          >
            <Menu size={20} />
          </button>
          <AnimatePresence>
            {drawerOpen && (
              <>
                <motion.div
                  className="drawer-overlay"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  onClick={() => setDrawerOpen(false)}
                />
                <motion.aside
                  className="sidebar sidebar-drawer"
                  initial={{ x: '-100%' }}
                  animate={{ x: 0 }}
                  exit={{ x: '-100%' }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                  onClick={() => setDrawerOpen(false)}
                >
                  <button
                    type="button"
                    className="icon-button drawer-close"
                    onClick={() => setDrawerOpen(false)}
                    aria-label="Close menu"
                  >
                    <X size={18} />
                  </button>
                  {sidebarContent}
                </motion.aside>
              </>
            )}
          </AnimatePresence>
        </>
      )}

      <main className="app-main">{children}</main>

      <CommandPalette namespaces={namespaces} />
    </div>
  )
}
