import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

function showBootError(msg: string) {
  const el = document.getElementById('boot-error');
  if (el) {
    el.style.display = 'block';
    el.textContent = msg;
  } else {
    // 兜底：输出到控制台
    console.error(msg);
  }
}

try {
  const rootEl = document.getElementById("root") as HTMLElement | null;
  if (!rootEl) throw new Error("找不到 #root 容器");
  ReactDOM.createRoot(rootEl).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
} catch (err: any) {
  showBootError(`应用启动失败: ${err?.message || String(err)}`);
}
