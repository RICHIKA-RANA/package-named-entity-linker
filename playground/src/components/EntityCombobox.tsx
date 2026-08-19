import { useState } from 'react'
import * as Popover from '@radix-ui/react-popover'
import { Command } from 'cmdk'
import { ChevronDown } from 'lucide-react'
import type { Entity } from '../api'

interface EntityComboboxProps {
  entities: Entity[]
  value: string
  onChange: (entityId: string) => void
  placeholder?: string
}

export default function EntityCombobox({
  entities,
  value,
  onChange,
  placeholder = 'Select an entity…',
}: EntityComboboxProps) {
  const [open, setOpen] = useState(false)

  return (
    <Popover.Root open={open} onOpenChange={setOpen}>
      <Popover.Trigger asChild>
        <button type="button" className="combobox-trigger">
          <span>{value || placeholder}</span>
          <ChevronDown size={14} />
        </button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content className="combobox-popover" align="start" sideOffset={4}>
          <Command>
            <Command.Input placeholder="Search entities…" autoFocus />
            <Command.List>
              <Command.Empty>No entities found.</Command.Empty>
              {entities.map((entity) => (
                <Command.Item
                  key={entity.entity_id}
                  value={`${entity.entity_id} ${entity.label}`}
                  onSelect={() => {
                    onChange(entity.entity_id)
                    setOpen(false)
                  }}
                >
                  {entity.label} ({entity.entity_id})
                </Command.Item>
              ))}
            </Command.List>
          </Command>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  )
}
