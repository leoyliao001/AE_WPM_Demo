# 本机部署说明

本项目在公司 Windows 服务器上的部署方式、服务名、以及**以后如何加其他项目（如 AE_SCAN）**，见总文档：

**[`E:\Apps\DEPLOYMENT.md`](../Apps/DEPLOYMENT.md)**

摘要：

- 前端大门：Windows 服务 **AE_Front_All**（Apache，端口 80）
- 本项目后端：Windows 服务 **AE_WPM**（Waitress，`127.0.0.1:8000`）
- 内网访问：`http://10.176.115.28/`
