import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

export type DownloadProgress = number

export interface API {
  getDefaultDownloadPath: () => Promise<string>
  selectDirectory: () => Promise<string>
  checkBackend: () => Promise<boolean>
  downloadBackend: (path: string, onProgress: (progress: DownloadProgress) => void) => Promise<boolean>
  startBackend: () => Promise<boolean>
  completeEnvCheck: (success: boolean) => void
}

const api: API = {
  getDefaultDownloadPath: () => ipcRenderer.invoke('get-default-download-path'),
  selectDirectory: () => ipcRenderer.invoke('select-directory'),
  checkBackend: () => ipcRenderer.invoke('check-backend'),
  downloadBackend: (path: string, onProgress: (progress: DownloadProgress) => void) => {
    ipcRenderer.on('download-progress', (_event, progress) => onProgress(progress))
    return ipcRenderer.invoke('download-backend', path)
  },
  startBackend: () => ipcRenderer.invoke('start-backend'),
  completeEnvCheck: (success: boolean) => ipcRenderer.send('env-check-complete', success)
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', electronAPI)
    contextBridge.exposeInMainWorld('api', api)
  } catch (error) {
    console.error('Failed to expose API:', error)
  }
} else {
  // @ts-ignore (define in dts)
  window.electron = electronAPI
  // @ts-ignore (define in dts)
  window.api = api
}
