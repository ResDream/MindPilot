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
  private static readonly DOWNLOAD_URL = 'https://mindpilot.obs.cn-north-4.myhuaweicloud.com/mindpilot.exe'
  private static readonly MAX_RETRIES = 30
  private static readonly RETRY_INTERVAL = 1000
  private static readonly TIMEOUT = 2000
  private notificationDebounce = false

  constructor(configManager: ConfigManager) {
    this.configManager = configManager
  }

  // 显示通知,添加防抖
  private showNotification(title: string, body: string) {
    if (this.notificationDebounce) return

    this.notificationDebounce = true
    const notification = new Notification({ title, body })
    notification.show()

    setTimeout(() => {
      this.notificationDebounce = false
    }, 3000)
  }

  // 检查后端是否运行
  public async checkBackend(): Promise<boolean> {
    try {
      const response = await axios.get(BackendManager.BACKEND_URL, {
        timeout: BackendManager.TIMEOUT
      })
      return response.status === 200
    } catch {
      return false
    }
  }

  // 下载后端程序
  public async downloadBackend(downloadPath: string, onProgress?: DownloadProgressCallback): Promise<boolean> {
    try {
      this.showNotification('开始下载', '正在下载后端程序...')

      const response = await axios({
        url: BackendManager.DOWNLOAD_URL,
        method: 'GET',
        responseType: 'stream',
        timeout: 0 // 下载不设超时
      })

      const totalLength = parseInt(response.headers['content-length'], 10)
      if (isNaN(totalLength)) {
        throw new Error('无法获取文件大小')
      }

      // 确保下载目录存在
      const dir = path.dirname(downloadPath)
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true })
      }

      return new Promise((resolve, reject) => {
        let downloaded = 0
        const writer = fs.createWriteStream(downloadPath)

        response.data.on('data', (chunk: Buffer) => {
          downloaded += chunk.length
          if (onProgress) {
            onProgress(Math.round((downloaded * 100) / totalLength))
          }
        })

        writer.on('finish', () => {
          this.showNotification('下载完成', '后端程序下载成功!')
          resolve(true)
        })

        writer.on('error', (err) => {
          fs.unlink(downloadPath, () => {})
          this.showNotification('下载失败', '下载过程中发生错误')
          reject(err)
        })

        response.data.pipe(writer)
      })

    } catch (error) {
      console.error('下载失败:', error)
      return false
    }
  }

  // 启动后端程序
  public async startBackend(): Promise<boolean> {
    try {
      const backendPath = this.configManager.getBackendPath()

      // 检查文件是否存在
      if (!this.configManager.checkBackendExists()) {
        throw new Error('找不到后端程序')
      }

      this.showNotification('启动中', '正在启动后端服务...')

      // 启动后端进程
      const process = spawn(backendPath, {
        detached: false,
        stdio: 'pipe',
        windowsHide: true
      })

      // 日志记录
      process.stdout?.on('data', (data) => console.log(`Backend stdout: ${data}`))
      process.stderr?.on('data', (data) => console.error(`Backend stderr: ${data}`))
      process.on('error', (error) => console.error('Backend process error:', error))

      // 等待后端启动
      for (let i = 0; i < BackendManager.MAX_RETRIES; i++) {
        await new Promise(r => setTimeout(r, BackendManager.RETRY_INTERVAL))
        if (await this.checkBackend()) {
          this.showNotification('启动成功', '后端服务已启动!')
          return true
        }
      }

      this.showNotification('启动失败', '后端服务启动超时')
      return false

    } catch (error) {
      console.error('启动失败:', error)
      this.showNotification('启动失败', String(error))
      return false
    }
  }
}
