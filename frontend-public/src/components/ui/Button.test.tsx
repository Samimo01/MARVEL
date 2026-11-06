import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import Button from './Button.tsx'

describe('Button', () => {
  it('signale le clic par un callback', async () => {
    const onClick = vi.fn()
    render(<Button onClick={onClick}>Valider</Button>)
    await userEvent.click(screen.getByRole('button', { name: 'Valider' }))
    expect(onClick).toHaveBeenCalledOnce()
  })
})
