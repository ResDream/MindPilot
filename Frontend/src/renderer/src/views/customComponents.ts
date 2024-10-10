export class JsonCollapse extends HTMLElement {
  private header: HTMLDivElement | null = null
  private content: HTMLDivElement | null = null

  constructor() {
    super()
    this.attachShadow({ mode: 'open' })
    this.shadowRoot!.innerHTML = `
      <style>
        :host {
          display: block;
          border: 1px solid #ccc;
          border-radius: 8px;
          font-family: 'Courier New', Courier, monospace;
        }
        #header {
          background-color: #f1f1f1;
          padding: 2px;
          cursor: pointer;
          font-size: 14px;
        }
        #content {
          padding: 10px;
          display: none;
          white-space: pre-wrap;
          background-color: #f9f9f9;
        }
      </style>
      <div id="header">${this.getAttribute('label') || 'JSON'}</div>
      <div id="content"></div>
    `

    this.header = this.shadowRoot!.querySelector('#header')
    this.content = this.shadowRoot!.querySelector('#content')

    this.header?.addEventListener('click', this.toggleContent.bind(this))
  }

  connectedCallback() {
    this.renderJson()
  }

  static get observedAttributes() {
    return ['data-json']
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  attributeChangedCallback(name: string, _oldValue: string, _newValue: string) {
    if (name === 'data-json') {
      this.renderJson()
    }
  }

  private toggleContent() {
    if (this.content) {
      this.content.style.display = this.content.style.display === 'block' ? 'none' : 'block'
    }
  }

  private renderJson() {
    const json = this.getAttribute('data-json')
    if (this.content) {
      try {
        const obj = JSON.parse(json || '{}')
        const formattedJson = JSON.stringify(obj, null, 2)
        this.content.textContent = formattedJson
      } catch (e) {
        this.content.textContent = 'Invalid JSON'
      }
    }
  }
}

export class MessageCollapse extends HTMLElement {
  private header: HTMLDivElement | null = null
  private content: HTMLDivElement | null = null
  private isCollapsed = true

  constructor() {
    super()
    this.attachShadow({ mode: 'open' })
    this.shadowRoot!.innerHTML = `
      <style>
        :host {
          display: block;
          border: 1px solid #ccc;
          border-radius: 8px;
          font-family: 'Arial', sans-serif;
        }
        #header {
          background-color: #f1f1f1;
          padding: 10px;
          cursor: pointer;
          font-size: 14px;
        }
        #content {
          padding: 10px;
          display: none;
          white-space: pre-wrap;
          background-color: #f9f9f9;
        }
      </style>
      <div id="header"></div>
      <div id="content"></div>
    `

    this.header = this.shadowRoot!.querySelector('#header')
    this.content = this.shadowRoot!.querySelector('#content')

    this.header?.addEventListener('click', this.toggleContent.bind(this))
  }

  connectedCallback() {
    this.renderMessage()
  }

  static get observedAttributes() {
    return ['data-message']
  }

  attributeChangedCallback(name: string, _oldValue: string, _newValue: string) {
    console.log(_oldValue, _newValue)
    if (name === 'data-message') {
      this.renderMessage()
    }
  }

  private toggleContent() {
    if (this.content) {
      this.isCollapsed = !this.isCollapsed
      this.content.style.display = this.isCollapsed ? 'none' : 'block'
      this.header!.textContent = this.isCollapsed
        ? this.getCollapsedMessage()
        : this.getFullMessage()
    }
  }

  private renderMessage() {
    const message = this.getAttribute('data-message') || ''
    if (this.header && this.content) {
      this.header.textContent = this.getCollapsedMessage()
      this.content.textContent = message
    }
  }

  private getCollapsedMessage() {
    const message = this.getAttribute('data-message') || ''
    return message.length > 50 ? message.substring(0, 50) + '...' : message
  }

  private getFullMessage() {
    return this.getAttribute('data-message') || ''
  }
}
