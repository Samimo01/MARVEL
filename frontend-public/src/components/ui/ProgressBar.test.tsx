import { render, screen } from '@testing-library/react'

import ProgressBar from './ProgressBar.tsx'

describe('ProgressBar', () => {
  it('expose la valeur de manière accessible', () => {
    render(<ProgressBar value={25} max={100} label="Campagne test" />)
    const bar = screen.getByRole('progressbar', { name: 'Campagne test' })
    expect(bar).toHaveAttribute('aria-valuenow', '25')
    expect(bar.firstElementChild).toHaveStyle({ width: '25%' })
  })

  it('plafonne la jauge à 100 % et gère un objectif nul', () => {
    const { rerender } = render(<ProgressBar value={150} max={100} label="Dépassée" />)
    expect(screen.getByRole('progressbar').firstElementChild).toHaveStyle({
      width: '100%',
    })

    rerender(<ProgressBar value={10} max={0} label="Sans objectif" />)
    expect(screen.getByRole('progressbar').firstElementChild).toHaveStyle({ width: '0%' })
  })
})
