import axios from 'axios'
import * as fs from 'fs'
import * as path from 'path'
import { spawn } from 'child_process'
import { Notification } from 'electron'
import { ConfigManager } from './configManager'

export interface DownloadProgressCallback {
  (progress: number): void
}

export class BackendManager {
  private configManager: ConfigManager
  private static readonly BACKEND_URL = 'http://127.0.0.1:7861/docs'
  private static readonly DOWNLOAD_URL =
    'https://mindpilot.obs.cn-north-4.myhuaweicloud.com/mindpilot.exe'
  private static readonly MAX_RETRIES = 30
  private static readonly RETRY_INTERVAL = 1000
  private static readonly TIMEOUT = 2000
  private notificationShown: boolean = false

  constructor(configManager: ConfigManager) {
    this.configManager = configManager
  }

  private showNotification(title: string, body: string) {
    // 避免重复显示通知
    if (!this.notificationShown) {
      const notification = new Notification({
        title,
        body,
        silent: false, // 是否播放声音
        timeoutType: 'default'
      })
      notification.show()
      this.notificationShown = true

      // 5秒后重置通知状态，允许再次显示
      setTimeout(() => {
        this.notificationShown = false
      }, 5000)
    }
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
      this.showNotification('下载开始', '正在下载后端程序...')
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

        writer.on('finish', () => {
          this.showNotification('下载完成', '后端程序下载成功！')
          resolve(true)
        })
        writer.on('error', (err) => {
          this.showNotification('下载失败', '后端程序下载失败，请重试！')
          fs.unlink(downloadPath, () => reject(err))
        })

        response.data.pipe(writer)

        // Add timeout
        setTimeout(
          () => {
            writer.close()
            this.showNotification('下载超时', '下载超时，请检查网络后重试！')
            reject(new Error('Download timeout'))
          },
          5 * 60 * 1000
        ) // 5 minutes timeout
      })
    } catch (error) {
      console.error('Download failed:', error)
      this.showNotification('下载出错', '下载过程中发生错误，请重试！')
      return false
    }
  }

  public async startBackend(): Promise<boolean> {
    try {
      const backendPath = this.configManager.getBackendPath()
      if (!fs.existsSync(backendPath)) {
        throw new Error('Backend executable not found')
      }

      this.showNotification('启动中', '正在启动MindPilot服务...')

      // 修改后的代码
      const process = spawn(backendPath, {
        detached: false,
        stdio: 'pipe',
        windowsHide: true
      })
      process.stdout?.on('data', (data) => {
        console.log(`Backend stdout: ${data}`)
      })
      process.stderr?.on('data', (data) => {
        console.error(`Backend stderr: ${data}`)
      })
      process.on('exit', (code) => {
        console.log(`Backend process exited with code ${code}`)
      })

      // Check if backend starts successfully
      for (let i = 0; i < BackendManager.MAX_RETRIES; i++) {
        await new Promise((resolve) => setTimeout(resolve, BackendManager.RETRY_INTERVAL))
        if (await this.checkBackend()) {
          this.configManager.updateStartStatus(true)
          this.showNotification('启动成功', '后端服务已成功启动！')
          return true
        }
      }

      this.configManager.updateStartStatus(false)
      this.showNotification('启动失败', '后端服务启动失败，请重试！')
      return false
    } catch (error) {
      console.error('Start backend failed:', error)
      this.configManager.updateStartStatus(false)
      this.showNotification('启动错误', '启动过程中发生错误，请检查配置！')
      return false
    }
  }
}
