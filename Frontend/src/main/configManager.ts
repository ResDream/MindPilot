import * as fs from 'fs'
import * as path from 'path'
import { app } from 'electron'

export class ConfigManager {
  private readonly configPath: string
  private readonly defaultBackendPath: string

  constructor() {
    // 配置文件保存在用户数据目录
    this.configPath = path.join(app.getPath('userData'), 'config.json')
    // 默认后端程序路径
    this.defaultBackendPath = path.join(app.getPath('userData'), 'mindpilot.exe')
  }

  // 获取后端程序路径
  public getBackendPath(): string {
    try {
      // 如果配置文件存在，读取配置
      if (fs.existsSync(this.configPath)) {
        const config = JSON.parse(fs.readFileSync(this.configPath, 'utf-8'))
        return config.backendPath || this.defaultBackendPath
      }
    } catch (error) {
      console.error('Failed to read config:', error)
    }
    return this.defaultBackendPath
  }

  // 设置后端程序路径
  public setBackendPath(backendPath: string): void {
    try {
      if (!backendPath) {
        throw new Error('Backend path cannot be empty')
      }

      // 确保配置目录存在
      const dir = path.dirname(this.configPath)
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true })
      }

      // 保存配置
      const config = { backendPath }
      fs.writeFileSync(this.configPath, JSON.stringify(config, null, 2))
    } catch (error) {
      console.error('Failed to save config:', error)
      throw error
    }
  }

  // 检查后端程序是否存在
  public checkBackendExists(): boolean {
    const backendPath = this.getBackendPath()
    return fs.existsSync(backendPath)
  }
}
