Final CI Review — 本地离线包
================================

【推荐】双击「打开页面.bat」启动本地服务并在浏览器中打开页面。

也可手动启动：
  cd /d "%~dp0"
  python -m http.server 8765
  浏览器访问 http://localhost:8765/Final-CI-Review.html

说明：
- 请勿直接双击 HTML 文件（浏览器安全限制会导致脚本无法加载）。
- 数据保存在浏览器 localStorage（key: automation_idea_records_v1）。
- 测试 Sign-off：在浏览器控制台执行
    localStorage.setItem('intake_requestor_email', 'vinod.gupta@maersk.com')
- MDS 字体/样式需联网加载 CDN 资源。
