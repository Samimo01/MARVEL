import { useCallback, useEffect, useState } from 'react'

export type AsyncState<T> =
  | { status: 'loading' }
  | { status: 'error'; error: Error }
  | { status: 'success'; data: T }

/** Hook générique : exécute une fonction asynchrone et expose son état. Sans lien métier. */
export function useAsync<T>(
  fn: () => Promise<T>,
): AsyncState<T> & { reload: () => void } {
  const [state, setState] = useState<AsyncState<T>>({ status: 'loading' })
  const [version, setVersion] = useState(0)

  useEffect(() => {
    let cancelled = false
    fn()
      .then((data) => !cancelled && setState({ status: 'success', data }))
      .catch((error: Error) => !cancelled && setState({ status: 'error', error }))
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version])

  const reload = useCallback(() => {
    setState({ status: 'loading' })
    setVersion((v) => v + 1)
  }, [])

  return { ...state, reload }
}
