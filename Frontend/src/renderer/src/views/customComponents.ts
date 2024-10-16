export class JsonCollapse extends HTMLElement {
  private header: HTMLDivElement | null = null
  private content: HTMLDivElement | null = null
  private arrow: HTMLSpanElement | null = null

  constructor() {
    super()
    this.attachShadow({ mode: 'open' })
    this.shadowRoot!.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: 'Arial', sans-serif;
          margin: 10px 0;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          overflow: hidden;
          transition: all 0.3s ease;
        }
        #header {
          background-color: #f0f4f8;
          padding: 12px 16px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 14px;
          font-weight: bold;
          color: #333;
          transition: background-color 0.3s ease;
        }
        #header:hover {
          background-color: #e3e9f2;
        }
        #content {
          max-height: 0;
          overflow: hidden;
          transition: max-height 0.3s ease;
          background-color: #fff;
        }
        #json-content {
          padding: 16px;
          margin: 0;
          white-space: pre-wrap;
          font-family: 'Consolas', monospace;
          font-size: 13px;
          color: #333;
        }
        .arrow {
          transition: transform 0.3s ease;
        }
        .arrow.open {
          transform: rotate(180deg);
        }
        .key { color: #881391; }
        .string { color: #1A1AA6; }
        .number { color: #1C00CF; }
        .boolean { color: #0000FF; }
        .null { color: #808080; }
      </style>
      <div id="header">
        <span>${this.getAttribute('label') || 'JSON'}</span>
        <span class="arrow">▼</span>
      </div>
      <div id="content">
        <pre id="json-content"></pre>
      </div>
    `

    this.header = this.shadowRoot!.querySelector('#header')
    this.content = this.shadowRoot!.querySelector('#content')
    this.arrow = this.shadowRoot!.querySelector('.arrow')

    this.header?.addEventListener('click', this.toggleContent.bind(this))
  }

  connectedCallback() {
    this.renderJson()
  }

  static get observedAttributes() {
    return ['data-json']
  }

  attributeChangedCallback(name: string, _oldValue: string, _newValue: string) {
    if (name === 'data-json') {
      this.renderJson()
    }
  }

  private toggleContent() {
    if (this.content && this.arrow) {
      const isOpen = this.content.style.maxHeight !== '0px'
      this.content.style.maxHeight = isOpen ? '0px' : `${this.content.scrollHeight}px`
      this.arrow.classList.toggle('open')
    }
  }

  private renderJson() {
    const json = this.getAttribute('data-json')
    const contentElement = this.shadowRoot!.querySelector('#json-content')
    if (contentElement) {
      try {
        const obj = JSON.parse(json || '{}')
        const formattedJson = this.syntaxHighlight(JSON.stringify(obj, null, 2))
        contentElement.innerHTML = formattedJson
      } catch (e) {
        contentElement.textContent = 'Invalid JSON'
      }
    }
  }

  private syntaxHighlight(json: string) {
    return json.replace(
      /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      (match) => {
        let cls = 'number'
        if (/^"/.test(match)) {
          if (/:$/.test(match)) {
            cls = 'key'
          } else {
            cls = 'string'
          }
        } else if (/true|false/.test(match)) {
          cls = 'boolean'
        } else if (/null/.test(match)) {
          cls = 'null'
        }
        return `<span class="${cls}">${match}</span>`
      }
    )
  }
}

export class MessageCollapse extends HTMLElement {
  private header: HTMLDivElement | null = null
  private content: HTMLDivElement | null = null
  private isCollapsed = true
  private arrow: HTMLSpanElement | null = null

  constructor() {
    super()
    this.attachShadow({ mode: 'open' })
    this.shadowRoot!.innerHTML = `
      <style>
        :host {
          display: block;
          font-family: 'Arial', sans-serif;
          margin: 10px 0;
          border-radius: 8px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          overflow: hidden;
          transition: all 0.3s ease;
        }
        #header {
          background-color: #e8f0fe;
          padding: 12px 16px;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: space-between;
          font-size: 14px;
          color: #1a73e8;
          transition: background-color 0.3s ease;
        }
        #header:hover {
          background-color: #d2e3fc;
        }
        #content {
          max-height: 0;
          overflow: hidden;
          transition: max-height 0.3s ease;
          background-color: #fff;
        }
        #message-content {
          padding: 16px;
          margin: 0;
          white-space: pre-wrap;
          font-size: 14px;
          line-height: 1.5;
          color: #202124;
        }
        .arrow {
          transition: transform 0.3s ease;
        }
        .arrow.open {
          transform: rotate(180deg);
        }
        .highlight {
          background-color: #ffeeba;
          padding: 2px 4px;
          border-radius: 4px;
        }
      </style>
      <div id="header">
        <span id="header-text"></span>
        <span class="arrow">▼</span>
      </div>
      <div id="content">
        <div id="message-content"></div>
      </div>
    `

    this.header = this.shadowRoot!.querySelector('#header')
    this.content = this.shadowRoot!.querySelector('#content')
    this.arrow = this.shadowRoot!.querySelector('.arrow')

    this.header?.addEventListener('click', this.toggleContent.bind(this))
  }

  connectedCallback() {
    this.renderMessage()
  }

  static get observedAttributes() {
    return ['data-message']
  }

  attributeChangedCallback(name: string, _oldValue: string, _newValue: string) {
    if (name === 'data-message') {
      this.renderMessage()
    }
  }

  private toggleContent() {
    if (this.content && this.arrow) {
      this.isCollapsed = !this.isCollapsed
      this.content.style.maxHeight = this.isCollapsed ? '0' : `${this.content.scrollHeight}px`
      this.arrow.classList.toggle('open')
      this.updateHeaderText()
    }
  }

  private renderMessage() {
    const message = this.getAttribute('data-message') || ''
    if (this.header && this.content) {
      this.updateHeaderText()
      const contentElement = this.shadowRoot!.querySelector('#message-content')
      if (contentElement) {
        contentElement.innerHTML = this.formatMessage(message)
      }
    }
  }

  private updateHeaderText() {
    const headerTextElement = this.shadowRoot!.querySelector('#header-text')
    if (headerTextElement) {
      headerTextElement.textContent = this.isCollapsed
        ? this.getCollapsedMessage()
        : 'Agent搜索结果'
    }
  }

  private getCollapsedMessage() {
    const message = this.getAttribute('data-message') || ''
    return message.length > 50 ? message.substring(0, 50) + '...' : message
  }

  private formatMessage(message: string) {
    // 简单的URL检测和链接转换
    const urlRegex = /(https?:\/\/[^\s]+)/g
    return message.replace(
      urlRegex,
      (url) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`
    )
  }
}
