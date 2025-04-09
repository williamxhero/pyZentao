# pyZentao 项目技术备忘录 (MEMO)

## 一、项目简介

pyZentao 是一个面向禅道项目管理系统的 **Python SDK**，支持通过 API 描述文件自动生成 RESTful 接口封装代码。  
其设计目标是：  
- **自动化生成**禅道 API 的 Python 封装，降低维护成本  
- 提供 **异步**、**分层封装** 的调用接口  
- 方便用户快速集成禅道 API，或基于此 SDK 进行二次开发

---

## 二、目录结构与文件功能

```
项目根目录
│
├── README.md                 # 项目简介
├── MEMO.md                   # 本技术备忘录
├── .gitignore
│
├── api_docs/                 # API 描述文件与代码生成工具
│   ├── zentao_api_docs.yaml  # 禅道 API 描述 (用户提供)
│   ├── openapi_generated.yaml# 生成的OpenAPI规范
│   ├── zentao-gen            # 生成工具 (命令行入口)
│   └── generate_sdk.py       # 生成脚本 (核心逻辑)
│
├── zentao_api/               # SDK 主体代码
│   ├── requirements.txt      # 依赖声明
│   │
│   ├── core/                 # **自动生成的底层代码**
│   │   ├── api/              # RESTful API 封装类 (每个资源一个类)
│   │   ├── models/           # 数据模型定义
│   │   └── client.py         # **底层异步客户端，动态挂载API类**
│   │
│   ├── client/               # 上层封装，面向用户的接口
│   │
│   ├── examples/             # 使用示例
│   │   └── all_opens.py      # 示例：登录禅道，调用API
│   │
│   └── tests/                # 测试代码
│
└── ...
```

---

## 三、代码生成机制

- **核心思想**：  
  通过用户提供的 `zentao_api_docs.yaml` ，描述禅道的API接口和数据结构。这个文件来源于工具 https://github.com/williamxhero/zentao_api_doc.git

- **生成流程**：  
  运行命令：
  ```
  python api_docs/zentao-gen -o ./zentao_api -d ./api_docs/zentao_api_docs.yaml
  ```
  或直接调用 `generate_sdk.py`，会：
  - 解析API描述文件
  - 自动生成：
    - `zentao_api/core/api/` 下的 **API封装类**，每个资源一个类，继承自 `BaseAPI`
    - `zentao_api/core/models/` 下的 **数据模型类**
  - 这些代码**禁止手工修改**，如需调整应修改API描述或生成脚本

- **优点**：
  - 快速适配禅道API变更
  - 保持接口一致性
  - 降低维护成本

---

## 四、底层客户端设计 (`zentao_api/core/client.py`)

### 1. ZentaoClient 类

- **职责**：
  - 管理 HTTP 会话
  - 统一封装请求发送
  - **动态扫描并挂载所有API类**

- **初始化**：
  - 传入 `base_url`、`username`、`password`
  - 自动扫描 `core/api/` 目录
  - 找到所有继承自 `BaseAPI` 的API类
  - 实例化后挂载为自身属性，如 `client.story`、`client.bug`、`client.tokens` 等

- **请求流程**：
  - 通过 `_request()` 方法封装HTTP请求
  - 自动拼接URL，附加认证信息
  - 支持路径参数、查询参数、请求体
  - 返回JSON响应
  - 使用 `aiohttp` 实现异步请求

- **关闭**：
  - `close()` 方法关闭aiohttp会话

### 2. API调用示例

```python
client = ZentaoClient(base_url, username, password)
response = await client.tokens.tokens(account=username, password=password)
await client.close()
```

本地zentao URL: http://192.168.0.72/zentao, 用户名：the_account，密码：the_password
---

## 五、示例代码说明 (`zentao_api/examples/all_opens.py`)

- 初始化 `ZentaoClient`
- 调用 `client.tokens.tokens()` 登录禅道，获取token
- 打印响应
- 关闭客户端

**示例体现了：**  
- SDK的异步调用方式  
- API类的动态挂载机制  
- 认证参数的传递方式

---

## 六、设计亮点

- **自动生成代码**：避免手写繁琐的API封装，适应API变更
- **异步支持**：基于 `aiohttp`，适合高并发场景
- **动态挂载API类**：无需手工注册，自动识别所有API资源
- **分层设计**：
  - **core层**：底层API封装，自动生成
  - **client层**：上层管理类，供用户调用
- **易扩展**：只需更新API描述文件和生成工具，即可适配新版本禅道

---

## 七、注意事项

- **禁止直接修改**：
  - `zentao_api/core/api/` 和 `zentao_api/core/models/` 下的代码，
    - 应通过修改生成工具来调整
  - `api_docs/zentao_api_docs.yaml` 
    - 应联系用户重新提供
- **API描述文件**：
  - 由用户根据禅道版本提供
  - 格式支持yaml/json
- **认证信息**：
  - 通过请求参数自动附加
- **异步调用**：
  - SDK基于asyncio，需在异步环境中使用

---

## 八、总结

pyZentao 是一个结构清晰、自动化程度高的禅道Python SDK。  
其核心在于**自动生成底层API封装**，并通过**异步客户端**统一管理，方便用户快速集成和调用禅道API。  
理解其**生成机制**和**动态挂载设计**，是后续维护和优化的关键。

---

## 九、代码生成改进建议

针对当前自动生成的代码，建议在后续优化生成工具时，重点关注以下两点：

### 1. 命名规范统一

- 目前 `core/api/base.py` 中的基类命名为 **`BaseAPI`**，而 `core/models/base.py` 中的基类命名为 **`ZentaoModel`**。
- 为保持一致性和直观理解，建议将 `ZentaoModel` 更名为 **`BaseModel`**。
- 这样有助于后续开发者快速识别基类角色，符合常见命名习惯。

### 2. 精简未使用的 imports

- 生成的 models 文件（如 `bugsresponse.py`）中，存在大量未被实际使用的导入：
  - 例如 `field`、`List`、`Dict`、`Any`、`datetime`、`date` 等
- 这些 imports 可能是模板中预设的“全量导入”，但会导致代码臃肿。
- 建议优化生成逻辑：
  - **根据每个模型字段的实际类型，动态生成所需 imports**
  - 避免未使用的类型导入，提升代码整洁性和可维护性。

### 3. 实现方式建议

- 这两项优化应在 **`api_docs/generate_sdk.py`** 或 **`zentao-gen`** 的模板中实现
- **禁止直接手工修改** `core/api` 和 `core/models` 下的生成代码
- 通过改进生成工具，确保每次生成的代码都符合规范，避免重复劳动

---

## 十、维护建议

- 本 **MEMO.md** 是整个项目的重要知识库，  
  记录了架构设计、生成机制、注意事项和优化建议。
- **强烈建议** 后续开发者或Agent在修改、优化、遇到坑点时，  
  **及时更新此文档**，补充新的经验、决策和注意事项。
- 这样可以方便团队成员或其他Agent快速了解项目最新状态，  
  避免重复踩坑，提升协作效率。
- 记住：**重要信息写进MEMO，知识才能传承！**

---
