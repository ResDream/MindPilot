/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any>
  export default component
}

declare module '*.svg?component' {
  import { DefineComponent } from 'vue'
  // eslint-disable-next-line @typescript-eslint/no-explicit-any, @typescript-eslint/ban-types
  const component: DefineComponent<{}, {}, any>
  export default component
}

export type DownloadProgress = number

export interface API {
  getDefaultDownloadPath: () => Promise<string>
  selectDirectory: () => Promise<string>
  checkBackend: () => Promise<boolean>
  downloadBackend: (
    path: string,
    onProgress: (progress: DownloadProgress) => void
  ) => Promise<boolean>
  startBackend: () => Promise<boolean>
  completeEnvCheck: (success: boolean) => void
}

declare global {
  interface Window {
    api: API
  }
}
