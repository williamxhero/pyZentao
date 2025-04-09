# ZenTao API SDK

这是一个用于与禅道（ZenTao）项目管理系统进行交互的Python SDK库。该SDK通过禅道的RESTful API提供了一套完整的接口封装，使开发者能够轻松地在Python应用中集成禅道的功能。

## 项目概述

ZenTao API SDK是一个自动生成的Python库，它基于禅道API文档自动生成相应的API接口和数据模型。该SDK支持禅道的所有主要功能，包括但不限于：

- 用户认证与管理
- 项目与项目集管理
- 产品管理
- 执行与迭代管理
- 需求（故事）管理
- 任务管理
- Bug管理
- 测试用例与测试任务管理
- 反馈与工单管理

## 项目结构

```
zentao_api_proj/
├── api_docs/                  # API文档和生成工具
│   ├── zentao_api_docs.json   # 禅道API描述文件
│   ├── zentao-gen             # SDK生成工具脚本
│   ├── generate_sdk.py        # SDK生成核心逻辑
│   └── openapi_generated.yaml # OpenAPI格式的API文档
│
├── zentao_api/                # 生成的SDK代码
│   ├── core/                  # 核心实现
│   │   ├── api/               # API接口封装
│   │   ├── models/            # 数据模型
│   │   └── client.py          # API客户端
│   ├── client/                # 上层封装类
│   └── requirements.txt       # 依赖项
│
├── examples/                  # 使用示例
└── tests/                     # 测试代码
```

## 特性

- **自动生成**：基于API文档自动生成SDK，确保API接口的完整覆盖
- **类型安全**：使用Python类型注解，提供更好的IDE支持和代码提示
- **异步支持**：基于`aiohttp`实现异步API调用，提高性能
- **模型映射**：自动将API响应映射到Python数据类，方便访问和操作
- **完整文档**：每个API方法和数据模型都有详细的文档注释

## 安装要求

- Python 3.8+
- aiohttp >= 3.8.0
- typing-extensions >= 4.0.0

## 使用方法

### 1. 生成SDK

如果您有自己的禅道API文档，可以使用提供的生成工具来生成SDK：

```bash
python api_docs/zentao-gen -o ./zentao_api -d ./api_docs/zentao_api_docs.json
```

这将根据API文档生成SDK代码，并将其放置在`zentao_api/core`目录下。

### 2. 基本使用

以下是一个简单的使用示例：

```python
import asyncio
from zentao_api.core.client import ZentaoClient

async def main():
    # 初始化客户端
    client = ZentaoClient(
        base_url="https://your-zentao-url/zentao/",
        username="your-username",
        password="your-password"
    )

    try:
        # 登录并获取token
        token_response = await client.tokens.tokens(
            account="your-username",
            password="your-password"
        )
        print(f"登录成功，token: {token_response.token}")

        # 获取用户信息
        user_info = await client.user.user()
        print(f"当前用户: {user_info.account}")

        # 获取项目列表
        projects = await client.projects.projects()
        for project in projects:
            print(f"项目: {project.name}")

    except Exception as e:
        print(f"操作失败: {e}")
    finally:
        # 关闭客户端会话
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. API分组

SDK按照禅道API的功能分组组织代码，主要包括：

- `tokens` - 认证相关
- `user/users` - 用户管理
- `departments` - 部门管理
- `programs` - 项目集管理
- `projects` - 项目管理
- `products` - 产品管理
- `executions` - 执行/迭代管理
- `stories` - 需求/故事管理
- `tasks` - 任务管理
- `bugs` - 缺陷管理
- `testcases` - 测试用例管理
- `testtasks` - 测试任务管理
- `feedbacks` - 反馈管理
- `tickets` - 工单管理

每个分组都有对应的API类，如`TokensAPI`、`UsersAPI`等，这些类会自动挂载到`ZentaoClient`实例上。

## 开发说明

1. **不要直接修改生成的代码**：`core/api`和`core/models`目录下的文件是自动生成的，不应直接修改。如需修改，应当更新生成工具或API文档，然后重新生成。

2. **扩展SDK**：如需扩展SDK功能，可以在`client`目录下创建新的类，这些类可以使用`core`中的功能，但不会被自动生成工具覆盖。

## 许可证

[待定]

## 贡献指南

[待定]

## 联系方式

[待定]
