import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as Popover from '@radix-ui/react-popover'
import { Command } from 'cmdk'
import { ChevronsUpDown } from 'lucide-react'
import type { Namespace } from '../api'

export default function NamespaceSwitcher({
  namespaces,
  current,
}: {
  namespaces: Namespace[]
  current: string
}) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button type="button" className="namespace-switcher-trigger">
          <span>{current}</span>
          <ChevronsUpDown size={14} />
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content className="combobox-popover" align="start" sideOffset={4}>
          <Command>
            <Command.Input placeholder="Switch namespace…" autoFocus />
            <Command.List>
              <Command.Empty>No namespaces found.</Command.Empty>
              {namespaces.map((namespace) => (
                <Command.Item
                  key={namespace.name}
                  value={namespace.name}
                  onSelect={() => {
                    setOpen(false)
                    navigate(`/namespaces/${encodeURIComponent(namespace.name)}?left=train`)
                  }}
                >
                  {namespace.name}
                </Command.Item>
              ))}
            </Command.List>
          </Command>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  )
}
