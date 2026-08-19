import type { ComponentType } from 'react'
import * as DropdownMenu from '@radix-ui/react-dropdown-menu'
import { MoreVertical } from 'lucide-react'

export interface ActionMenuItem {
  label: string
  icon: ComponentType<{ size?: number }>
  onClick: () => void
  destructive?: boolean
}

export default function ActionMenu({ items }: { items: ActionMenuItem[] }) {
  return (
    <DropdownMenu.Root>
      <DropdownMenu.Trigger asChild>
        <button
          type="button"
          className="icon-button"
          aria-label="Actions"
          onClick={(event) => event.stopPropagation()}
        >
          <MoreVertical size={16} />
        </button>
      </DropdownMenu.Trigger>
      <DropdownMenu.Portal>
        <DropdownMenu.Content className="action-menu-content" align="end" sideOffset={4}>
          {items.map((item) => (
            <DropdownMenu.Item
              key={item.label}
              className={item.destructive ? 'action-menu-item destructive' : 'action-menu-item'}
              onSelect={(event) => {
                event.preventDefault()
                item.onClick()
              }}
            >
              <item.icon size={14} />
              {item.label}
            </DropdownMenu.Item>
          ))}
        </DropdownMenu.Content>
      </DropdownMenu.Portal>
    </DropdownMenu.Root>
  )
}
