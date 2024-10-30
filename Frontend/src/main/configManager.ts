import * as fs from 'fs'
import * as path from 'path'
import { app } from 'electron'

export interface BackendConfig {
  backendPath: string
  lastStartTime: string | null
  lastStartSuccess: boolean
  version: string
  customPath?: string
}

export class ConfigManager {
  private readonly configPath: string
  private config: BackendConfig
  private static readonly DEFAULT_VERSION = '1.0.0'

  constructor() {
    this.configPath = path.join(app.getPath('userData'), 'backend-config.json')
    this.config = this.loadConfig()
  }

  private loadConfig(): BackendConfig {
    try {
      if (fs.existsSync(this.configPath)) {
        const data = fs.readFileSync(this.configPath, 'utf-8')
        const parsedConfig = JSON.parse(data) as Partial<BackendConfig>
        return this.validateConfig(parsedConfig)
      }
    } catch (error) {
      console.error('Failed to load config:', error)
    }

    return this.getDefaultConfig()
  }

  private validateConfig(config: Partial<BackendConfig>): BackendConfig {
    const defaultConfig = this.getDefaultConfig()
    return {
      backendPath: config.backendPath || defaultConfig.backendPath,
      lastStartTime: config.lastStartTime || null,
      lastStartSuccess: Boolean(config.lastStartSuccess),
      version: config.version || ConfigManager.DEFAULT_VERSION,
      customPath: config.customPath
    }
  }

  private getDefaultConfig(): BackendConfig {
    return {
      backendPath: path.join(app.getPath('userData'), 'mindpilot.exe'),
      lastStartTime: null,
      lastStartSuccess: false,
      version: ConfigManager.DEFAULT_VERSION
    }
  }

  public saveConfig(): void {
    try {
      const dir = path.dirname(this.configPath)
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true })
      }
      fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2))
    } catch (error) {
      console.error('Failed to save config:', error)
      throw new Error('Failed to save configuration')
    }
  }

  public getBackendPath(): string {
    return this.config.customPath || this.config.backendPath
  }

  public setCustomPath(customPath: string): void {
    if (!customPath) {
      throw new Error('Custom path cannot be empty')
    }
    this.config.customPath = customPath
    this.saveConfig()
  }

  public updateStartStatus(success: boolean): void {
    this.config.lastStartTime = new Date().toISOString()
    this.config.lastStartSuccess = success
    this.saveConfig()
  }

  public wasLastStartSuccessful(): boolean {
    return this.config.lastStartSuccess
  }

  public getDefaultDownloadPath(): string {
    return this.config.backendPath
  }
}
