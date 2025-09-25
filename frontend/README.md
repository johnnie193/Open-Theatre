# Open Theatre - React Frontend

这是Open Theatre项目的React前端实现，完全复现了原始HTML/JavaScript版本的所有功能。

## 🚀 功能特性

### 核心功能
- **交互式对话系统** - 支持角色对话和动作交互
- **角色管理** - 动态添加/删除角色，上传头像，查看角色信息
- **场景管理** - 创建和管理多场景剧本，设置角色动机和剧情链
- **脚本管理** - 保存/加载脚本，导出记录
- **提示词管理** - 编辑和管理各种AI提示词
- **信息面板** - 显示脚本、角色、系统反馈和记录信息

### 高级UI特性
- **现代化设计** - 使用shadcn/ui组件库
- **动画效果** - 流畅的动画和过渡效果
- **3D视觉效果** - 3D卡片和粒子背景
- **主题切换** - 支持浅色/深色主题
- **响应式设计** - 适配各种屏幕尺寸
- **语音功能** - 语音输入和文本转语音
- **魔法效果** - 发送消息时的粒子动画

## 🛠️ 技术栈

- **React 18** - 前端框架
- **TypeScript** - 类型安全
- **Tailwind CSS** - 样式框架
- **shadcn/ui** - UI组件库
- **Framer Motion** - 动画库
- **Lucide React** - 图标库

## 📦 安装和运行

### 前置要求
- Node.js 16+
- npm 或 yarn
- Python Flask后端服务

### 安装依赖
```bash
cd frontend
npm install
```

### 启动开发服务器
```bash
npm run dev
```

### 构建生产版本
```bash
npm run build
```

## 🔧 配置

### 后端API配置
在 `src/services/api.ts` 中修改 `baseUrl` 以匹配你的Flask后端地址：
```typescript
private baseUrl = 'http://localhost:5000'; // 修改为你的后端地址
```

### 静态资源
角色头像等静态资源已放置在 `public/assets/` 目录下，确保Flask后端也提供相同的静态文件。

## 📁 项目结构

```
frontend/
├── src/
│   ├── components/           # React组件
│   │   ├── ui/              # shadcn/ui基础组件
│   │   ├── CharacterManagement.tsx
│   │   ├── SceneManagement.tsx
│   │   ├── ScriptManagement.tsx
│   │   ├── PromptManagement.tsx
│   │   ├── InfoPanels.tsx
│   │   └── GameInterface.tsx
│   ├── services/            # API服务
│   │   └── api.ts
│   ├── lib/                 # 工具函数
│   │   └── utils.ts
│   └── App.tsx              # 主应用组件
├── public/
│   └── assets/              # 静态资源
└── package.json
```

## 🎮 使用说明

### 1. 游戏界面
- 选择动作类型（-stay 或 -speak）
- 输入消息内容
- 选择目标角色（可选）
- 点击发送按钮或按Enter键发送

### 2. 角色管理
- 添加新角色并设置档案
- 上传角色头像
- 查看角色详细信息、记忆和系统块

### 3. 场景管理
- 创建新场景并设置背景信息
- 选择架构模式（v1, v2, v2_plus等）
- 设置角色动机和剧情链

### 4. 脚本管理
- 保存当前脚本配置
- 加载已保存的脚本
- 导出游戏记录

### 5. 提示词管理
- 编辑各种AI提示词
- 保存提示词设置

## 🔄 与原始版本的对应关系

| 原始功能 | React实现 |
|---------|-----------|
| `gameMain.js` | `GameInterface.tsx` |
| `infoManager.js` | `InfoPanels.tsx` |
| `utils.js` | `CharacterManagement.tsx`, `SceneManagement.tsx` |
| `scriptManager.js` | `ScriptManagement.tsx` |
| `loadScript.js` | `ScriptManagement.tsx` |
| `saveScript.js` | `ScriptManagement.tsx` |
| `promptManager.js` | `PromptManagement.tsx` |

## 🐛 故障排除

### 常见问题

1. **API连接失败**
   - 确保Flask后端服务正在运行
   - 检查 `api.ts` 中的 `baseUrl` 配置

2. **静态资源加载失败**
   - 确保 `public/assets/` 目录包含所有角色头像
   - 检查文件路径是否正确

3. **类型错误**
   - 运行 `npm run build` 检查TypeScript错误
   - 确保所有依赖都已正确安装

## 📝 开发说明

### 添加新功能
1. 在 `src/components/` 中创建新组件
2. 在 `src/services/api.ts` 中添加API方法
3. 在 `App.tsx` 中集成新组件

### 样式定制
- 使用Tailwind CSS类名
- 修改 `tailwind.config.js` 进行主题定制
- 使用shadcn/ui组件作为基础

### 状态管理
- 使用React的 `useState` 和 `useEffect`
- 通过props传递状态和回调函数
- 考虑使用Context API进行全局状态管理

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 📄 许可证

本项目遵循MIT许可证。