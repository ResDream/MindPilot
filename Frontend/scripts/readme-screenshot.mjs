import { chromium } from "playwright"
import { resolve } from "node:path"

const browser = await chromium.launch({ headless: true })
try {
  const page = await browser.newPage({ viewport: { width: 1560, height: 2050 }, deviceScaleFactor: 1 })
  const errors = []
  page.on("pageerror", (error) => errors.push(error.message))
  await page.goto("http://127.0.0.1:5173", { waitUntil: "networkidle" })
  await page.getByText("演示数据 · 多阶段任务").waitFor()
  await page.evaluate(async () => {
    await document.fonts.ready
    document.querySelector(".mp-timeline").scrollTop = 0
  })
  await page.addStyleTag({ content: ".mp-fade-up { animation: none !important; opacity: 1 !important; }" })
  const layout = await page.locator(".mp-timeline").evaluate((element) => ({
    height: element.clientHeight, content: element.scrollHeight
  }))
  if (layout.content > layout.height) {
    await page.setViewportSize({ width: 1560, height: 2050 + layout.content - layout.height + 40 })
  }
  if (errors.length) throw new Error(errors.join("\n"))
  const finalLayout = await page.locator(".mp-timeline").evaluate((element) => ({
    height: element.clientHeight, content: element.scrollHeight
  }))
  if (finalLayout.content > finalLayout.height) throw new Error("任务记录超出截图范围")
  if (await page.locator(".mp-assistant-text h2").count() !== 1) throw new Error("最终报告标题缺失")
  await page.screenshot({ path: resolve("../docs/images/home.png"), fullPage: true })
  console.log(JSON.stringify({ pageErrors: errors.length, taskRows: await page.locator(".mp-msg-row").count(), layout: finalLayout }))
} finally {
  await browser.close()
}
