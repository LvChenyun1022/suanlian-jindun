// Kimi Work 预览适配：将 npm run dev 的 --host/--port 参数转发给 Streamlit。
// 仅本地 localhost 运行，不做公网部署。
const { spawn } = require("child_process");

const args = process.argv.slice(2);
let host = "localhost";
let port = null;
for (let i = 0; i < args.length; i++) {
  if (args[i] === "--host" && args[i + 1]) host = args[i + 1];
  if (args[i] === "--port" && args[i + 1]) port = args[i + 1];
}
// 本地预览仅允许回环地址
if (host !== "localhost" && host !== "127.0.0.1") host = "localhost";

const cmd = ["run", "app/streamlit_app.py", "--server.headless", "true",
             "--server.address", host];
if (port) cmd.push("--server.port", String(port));

const child = spawn("streamlit", cmd, { stdio: "inherit", shell: true });
child.on("exit", (code) => process.exit(code ?? 0));
