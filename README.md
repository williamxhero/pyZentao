# pyZentao - 禅道 API SDK

这是一个用于与禅道（ZenTao）项目管理系统进行交互的Python SDK库。该SDK通过禅道的RESTful API提供了一套完整的接口封装，使开发者能够轻松地在Python应用中集成禅道的功能。

## 项目概述

pyZentao 是一个自动生成的Python SDK，它基于OpenAPI规范的禅道API文档自动生成相应的API接口和数据模型。该SDK支持禅道的所有主要功能，包括但不限于：

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
pyZentao/
├── api_docs/                  # API文档和生成工具
│   ├── zentao_api_docs.yaml   # OpenAPI格式的API文档（由zentao_api_doc工具生成）
│   ├── zentao-gen             # SDK生成工具脚本
│   └── generate_sdk.py        # SDK生成核心逻辑
│
├── zentao_api/                # 生成的SDK代码
│   ├── core/                  # 自动生成的底层代码
│   │   ├── api/               # API接口封装类 (每个资源一个类)
│   │   ├── models/            # 数据模型定义
│   │   └── client.py          # 底层异步客户端，动态挂载API类
│   ├── client/                # 上层封装，面向用户的接口
│   ├── examples/              # 使用示例
│   │   └── all_opens.py       # 示例：登录禅道，调用API
│   ├── tests/                 # 测试代码
│   └── requirements.txt       # 依赖项
│
├── README.md                  # 项目说明文档
└── MEMO.md                    # 技术备忘录
```

## 特性

- **自动生成代码**：基于OpenAPI规范的API文档自动生成SDK，避免手写繁琐的API封装，适应API变更
- **类型安全**：使用Python类型注解，提供更好的IDE支持和代码提示
- **异步支持**：基于`aiohttp`实现异步API调用，适合高并发场景
- **动态挂载API类**：无需手工注册，自动识别所有API资源
- **模型映射**：自动将API响应映射到Python数据类，方便访问和操作
- **分层设计**：
  - **core层**：底层API封装，自动生成
  - **client层**：上层管理类，供用户调用
- **完整文档**：每个API方法和数据模型都有详细的文档注释

## 安装要求

- Python 3.8+
- aiohttp >= 3.8.0
- typing-extensions >= 4.0.0

## 使用方法

### 1. 生成API文档和SDK

#### 1.1 生成API文档

本项目中的 `zentao_api_docs.yaml` 文件是使用 [zentao_api_doc](https://github.com/williamxhero/zentao_api_doc.git) 工具生成的。如果您使用的禅道版本与当前库不同，需要按照以下步骤生成适用于您版本禅道的API文档：

1. 克隆 zentao_api_doc 仓库：
   ```bash
   git clone https://github.com/williamxhero/zentao_api_doc.git
   cd zentao_api_doc
   ```

2. 根据仓库中的说明，配置您的禅道实例信息并运行爬取脚本，生成 OpenAPI 规范文件。

3. 将生成的 OpenAPI 文件复制到本项目的 `api_docs/zentao_api_docs.yaml`。

#### 1.2 生成SDK

使用提供的生成工具来生成SDK：

```bash
python api_docs/zentao-gen -o ./zentao_api -d ./api_docs/zentao_api_docs.yaml
```

这将根据API文档生成SDK代码，并将其放置在`zentao_api/core`目录下。

> **注意：** 如果您使用的禅道版本与当前库不同，生成的API可能会有差异。请确保生成的SDK与您的禅道版本兼容。

### 2. 基本使用

以下是一个简单的使用示例：

```python
import asyncio
from zentao_api.core.client import ZentaoClient

async def main():
    # 初始化客户端
    client = ZentaoClient(
        base_url="http://your-zentao-url/zentao",
        username="your-username",
        password="your-password"
    )

    try:
        # 登录并获取token
        token_response = await client.tokens.postTokens(body={
            "account": "your-username",
            "password": "your-password"
        })
        print(f"登录成功，token: {token_response.token}")

        # 获取用户信息
        user_info = await client.user.getUser()
        print(f"当前用户: {user_info.account}")

        # 获取项目列表
        projects_response = await client.projects.getProjects()
        for project in projects_response.projects:
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

## 代码生成机制

- **核心思想**：通过用户提供的 `zentao_api_docs.yaml`，描述禅道的API接口和数据结构
- **生成流程**：
  - 解析API描述文件
  - 自动生成 `zentao_api/core/api/` 下的 **API封装类**，每个资源一个类，继承自 `BaseAPI`
  - 自动生成 `zentao_api/core/models/` 下的 **数据模型类**，继承自 `BaseModel`
  - 这些代码**禁止手工修改**，如需调整应修改API描述或生成脚本

## 底层客户端设计

`ZentaoClient` 类的主要职责：
- 管理 HTTP 会话
- 统一封装请求发送
- **动态扫描并挂载所有API类**

初始化时，客户端会：
- 传入 `base_url`、`username`、`password`
- 自动扫描 `core/api/` 目录
- 找到所有继承自 `BaseAPI` 的API类
- 实例化后挂载为自身属性，如 `client.story`、`client.bug`、`client.tokens` 等

## 开发说明

1. **不要直接修改生成的代码**：`core/api`和`core/models`目录下的文件是自动生成的，不应直接修改。如需修改，应当更新生成工具或API文档，然后重新生成。

2. **扩展SDK**：如需扩展SDK功能，可以在`client`目录下创建新的类，这些类可以使用`core`中的功能，但不会被自动生成工具覆盖。

## 常见问题

1. **API方法命名规则**：API方法名称遵循 `{method}{Resource}` 的格式，例如 `getProjects`、`postTokens`、`deleteBugs` 等。

2. **认证方式**：SDK使用Token认证，首先调用 `client.tokens.postTokens()` 获取token，后续请求会自动附加认证信息。

3. **异步调用**：SDK基于asyncio，需在异步环境中使用，所有API调用都是异步的，需要使用 `await` 关键字。

4. **禅道版本兼容性**：当前 SDK 基于禅道开源版 21.6.beta 生成。如果您使用的是其他版本禅道，需要使用 [zentao_api_doc](https://github.com/williamxhero/zentao_api_doc.git) 工具从您的禅道实例中爬取 API 文档，然后重新生成 SDK。
