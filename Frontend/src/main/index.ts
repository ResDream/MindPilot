import { app, shell, BrowserWindow, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import icon from '../../resources/icon.png?asset'
import { ConfigManager } from './configManager'
import { BackendManager } from './backendManager'

let mainWindow: BrowserWindow | null = null
let envCheckWindow: BrowserWindow | null = null
let configManager: ConfigManager
let backendManager: BackendManager

function createEnvCheckWindow(): void {
  envCheckWindow = new BrowserWindow({
    width: 600,
    height: 400,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      nodeIntegration: true,
      contextIsolation: true
    }
  })

  envCheckWindow.on('ready-to-show', () => {
    envCheckWindow?.show()
  })

  envCheckWindow.on('closed', () => {
    envCheckWindow = null
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    envCheckWindow.loadURL(`${process.env['ELECTRON_RENDERER_URL']}/env-check.html`)
  } else {
    envCheckWindow.loadFile(join(__dirname, '../renderer/env-check.html'))
  }
}

function createMainWindow(): void {
  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    show: false,
    autoHideMenuBar: true,
    ...(process.platform === 'linux' ? { icon } : {}),
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      webSecurity: false,
      contextIsolation: true
    }
  })

  mainWindow.on('ready-to-show', () => {
    mainWindow?.show()
  })

  mainWindow.on('closed', () => {
    mainWindow = null
  })

  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(join(__dirname, '../renderer/index.html'))
  }
}

function setupIPC() {
  ipcMain.handle('get-default-download-path', () => {
    return configManager.getDefaultDownloadPath()
  })

  ipcMain.handle('select-directory', async () => {
    const result = await dialog.showOpenDialog({
      properties: ['openDirectory']
    })
    return result.filePaths[0]
  })

  ipcMain.handle('check-backend', async () => {
    return await backendManager.checkBackend()
  })

  ipcMain.handle('download-backend', async (event, downloadPath: string) => {
    return await backendManager.downloadBackend(downloadPath, (progress) => {
      event.sender.send('download-progress', progress)
    })
  })

  ipcMain.handle('start-backend', async () => {
    return await backendManager.startBackend()
  })

  ipcMain.on('env-check-complete', (_event, success) => {
    if (success) {
      createMainWindow()
      if (envCheckWindow) {
        envCheckWindow.close()
      }
    } else {
      app.quit()
    }
  })
}

// Handle backend startup and window creation
async function handleStartup() {
  const backendAvailable = await backendManager.checkBackend()

  if (backendAvailable) {
    createMainWindow()
  } else if (configManager.wasLastStartSuccessful()) {
    const startSuccess = await backendManager.startBackend()
    if (startSuccess) {
      createMainWindow()
    } else {
      createEnvCheckWindow()
    }
  } else {
    createEnvCheckWindow()
  }
}

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.electron')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  // Initialize managers
  configManager = new ConfigManager()
  backendManager = new BackendManager(configManager)

  // Setup IPC handlers
  setupIPC()

  // Handle startup
  await handleStartup()

  app.on('activate', async function () {
    if (BrowserWindow.getAllWindows().length === 0) {
      const backendAvailable = await backendManager.checkBackend()
      if (backendAvailable) {
        createMainWindow()
      } else {
        createEnvCheckWindow()
      }
    }
  })
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

// Handle errors
process.on('uncaughtException', (error) => {
  console.error('Uncaught exception:', error)
})

process.on('unhandledRejection', (error) => {
  console.error('Unhandled rejection:', error)
})
