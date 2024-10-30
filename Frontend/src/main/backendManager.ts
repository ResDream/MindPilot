import axios from 'axios'
import * as fs from 'fs'
import * as path from 'path'
import { spawn } from 'child_process'
import { ConfigManager } from './configManager'

export interface DownloadProgressCallback {
  (progress: number): void
}

export class BackendManager {
  private configManager: ConfigManager
  private static readonly BACKEND_URL = 'http://127.0.0.1:7861/docs'
  private static readonly DOWNLOAD_URL = 'https://mindpilot.obs.cn-north-4.myhuaweicloud.com/mindpilot.exe'
  private static readonly MAX_RETRIES = 30
  private static readonly RETRY_INTERVAL = 1000
  private static readonly TIMEOUT = 2000

  constructor(configManager: ConfigManager) {
    this.configManager = configManager
  }

  public async checkBackend(): Promise<boolean> {
    try {
      const response = await axios.get(BackendManager.BACKEND_URL, {
        timeout: BackendManager.TIMEOUT,
        validateStatus: (status) => status === 200
      })
      return response.status === 200
    } catch {
      return false
    }
  }

  public async downloadBackend(
    downloadPath: string,
    onProgress?: DownloadProgressCallback
  ): Promise<boolean> {
    try {
      const response = await axios({
        url: BackendManager.DOWNLOAD_URL,
        method: 'GET',
        responseType: 'stream',
        timeout: BackendManager.TIMEOUT
      })

      const totalLength = parseInt(response.headers['content-length'], 10)
      if (isNaN(totalLength)) {
        throw new Error('Invalid content length')
      }

      const dir = path.dirname(downloadPath)
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true })
      }

      let downloaded = 0

      return new Promise((resolve, reject) => {
        const writer = fs.createWriteStream(downloadPath)

        response.data.on('data', (chunk: Buffer) => {
          downloaded += chunk.length
          if (onProgress && totalLength > 0) {
            onProgress(Math.round((downloaded * 100) / totalLength))
          }
        })

        writer.on('finish', () => resolve(true))
        writer.on('error', (err) => {
          fs.unlink(downloadPath, () => reject(err))
        })

        response.data.pipe(writer)

        // Add timeout
        setTimeout(() => {
          writer.close()
          reject(new Error('Download timeout'))
        }, 5 * 60 * 1000) // 5 minutes timeout
      })
    } catch (error) {
      console.error('Download failed:', error)
      return false
    }
  }

  public async startBackend(): Promise<boolean> {
    try {
      const backendPath = this.configManager.getBackendPath()
      if (!fs.existsSync(backendPath)) {
        throw new Error('Backend executable not found')
      }

      const process = spawn(backendPath, {
        detached: true,
        stdio: 'ignore',
        windowsHide: true
      })

      process.unref()

      // Check if backend starts successfully
      for (let i = 0; i < BackendManager.MAX_RETRIES; i++) {
        await new Promise(resolve => setTimeout(resolve, BackendManager.RETRY_INTERVAL))
        if (await this.checkBackend()) {
          this.configManager.updateStartStatus(true)
          return true
        }
      }

      this.configManager.updateStartStatus(false)
      return false
    } catch (error) {
      console.error('Start backend failed:', error)
      this.configManager.updateStartStatus(false)
      return false
    }
  }
}
