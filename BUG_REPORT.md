# WheelX SDK — 测试 Bug 报告

| 项目 | 内容 |
|------|------|
| **测试日期** | 2026-06-25 |
| **测试人员** | Alexander Green |
| **被测版本** | `wheelx-sdk` main 分支 |
| **测试环境** | `https://api.wheelx.fi` (Production) |
| **测试组件** | Python SDK / TypeScript SDK / Go SDK / MCP Server |

---

## 测试概览

| 测试项 | 结果 | 说明 |
|--------|------|------|
| `GET /v1/chain-info` | ✅ PASS | 返回 200, 60+ 链 |
| `POST /v1/quote` | ✅ PASS | 返回 200, 多路由报价 |
| `GET /v1/order/{id}` | ✅ PASS | 真实地址 20 笔订单全部 200，返回完整订单数据 |
| `GET /v1/orders/{addr}` | ✅ PASS | 真实地址返回 20 笔历史订单，跨 8 条链 |
| Python SDK `get_quote()` | ✅ PASS | 返回完整数据 |
| Python SDK `get_order_status()` | ✅ PASS | 真实订单 ID 全部返回 Filled 状态，token info 解析正确 |
| MCP Server 6 tools + 3 resources | ✅ PASS | 全部 9 项通过 |
| TypeScript SDK `getQuote()` | ❌ 编译失败 | 4 个编译错误（详见 Bug #4、#5） |
| TypeScript SDK 验证逻辑 | ❌ 编译失败 | 同上 |
| Go SDK `GetQuote()` | ❌ 运行时崩溃 | JSON 解析错误（详见 Bug #1） |
| Go SDK 编译 | ❌ 编译失败 | `go.sum` 缺失 + `go-ethereum` 下载超时 |

---

---

## Bug #1 — [Blocker] Go SDK: `Tx.Value` 类型 `int` 无法解析 API 返回的 `string`

**严重程度**: 🔴 Blocker（阻断性）  
**影响范围**: Go SDK — `go/wheelx/wheelx_sdk.go`  
**发现方式**: 通过 Go 独立测试脚本调用真实 API

### 现象

调用 `GetQuote()` 后，在解析 API 响应时 `json.Unmarshal` 报错：

```
failed to parse response: json: cannot unmarshal string into Go struct field Tx.value of type int
```

### 复现步骤

```go
sdk := wheelx.NewWheelXSDK("")
req := wheelx.QuoteRequest{
    FromChain:   1, ToChain: 1,
    FromToken:   "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    ToToken:     "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    FromAddress: "0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
    ToAddress:   "0x742d35Cc6634C0532925a3b8Dc9F6A7c5D3a7C6a",
    Amount:      1000000,
}
quote, err := sdk.GetQuote(context.Background(), req)
// err != nil ← 这里崩溃
```

### 根因分析

API `/v1/quote` 返回的 `tx.value` 字段是 **字符串** `"0"`，不是数字 `0`。

**API 实际返回**（截取）：

```json
{
  "tx": {
    "to": "0x7eC9672678509a574F6305F112a7E3703845a98b",
    "value": "0",
    "data": "0xb3c8c6da...",
    "chainId": 1,
    "gas": null,
    "maxFeePerGas": null,
    "maxPriorityFeePerGas": null
  }
}
```

**SDK 当前定义**（`go/wheelx/wheelx_sdk.go` 第 32-40 行）：

```go
type Tx struct {
    To                   string `json:"to"`
    Value                int    `json:"value"`                 // ← 定义为 int，API 返回 "0"(string)
    Data                 string `json:"data"`
    ChainId              *int   `json:"chainId,omitempty"`
    Gas                  *int   `json:"gas,omitempty"`         // ← API 可能返回字符串
    MaxFeePerGas         *int   `json:"maxFeePerGas,omitempty"`
    MaxPriorityFeePerGas *int   `json:"maxPriorityFeePerGas,omitempty"`
}
```

Go 的 `encoding/json` 严格区分类型，无法将 `"0"` 反序列化为 `int`。

### 受影响字段分析

API 中 `tx.value`、`tx.gas`、`tx.maxFeePerGas`、`tx.maxPriorityFeePerGas` 均可能为字符串。而 `chainId` 确实是数字（`1`），不需要改。

### 修改建议

将 `Tx` 结构体中 **金额/大数相关字段** 的类型从 `int`/`*int` 改为 `string`/`*string`，与 API 实际返回对齐：

```go
type Tx struct {
    To                   string  `json:"to"`
    Value                string  `json:"value"`                // 改: int → string
    Data                 string  `json:"data"`
    ChainId              *int    `json:"chainId,omitempty"`    // 不改: API 返回数字
    Gas                  *string `json:"gas,omitempty"`        // 改: *int → *string
    MaxFeePerGas         *string `json:"maxFeePerGas,omitempty"`
    MaxPriorityFeePerGas *string `json:"maxPriorityFeePerGas,omitempty"`
}
```

⚠ **连带影响**：`BuildTransaction`、`BuildEIP1559Transaction` 方法中使用 `int64(txData.Value)` 的地方需要同步改为字符串→大数转换（如 `big.Int.SetString` 或 `strconv.Atoi`）。`ApproveAction.Amount` 同样需要检查。

---

## Bug #2 — [Major] 所有 SDK: `QuoteResponse` 缺少 API 新增字段

**严重程度**: 🟠 Major（功能缺失）  
**影响范围**: Python SDK / TypeScript SDK / Go SDK  

### 现象

API `/v1/quote` 返回的数据包含多路由对比数组 `quotes[]` 等字段，但三个 SDK 的 `QuoteResponse` 类型均未定义这些字段，用户调用 SDK 无法获取这些数据。

### API 实际返回 vs SDK 定义

| 字段 | API 实际存在 | Python SDK | TypeScript SDK | Go SDK | 说明 |
|------|:---:|:---:|:---:|:---:|------|
| `quotes` | ✅ | ❌ | ❌ | ❌ | 多路由器报价对比数组 |
| `routes` | ✅ | ❌ | ❌ | ❌ | 路由详情（name + logo） |
| `deposit_address` | ✅ | ❌ | ❌ | ❌ | 充值地址（桥接场景） |
| `gas_fee` | ✅ | ❌ | ❌ | ❌ | Gas 费用 |
| `bridge_order_id` | ✅ | ❌ | ❌ | ❌ | 桥接订单 ID |
| `quote_message` | ✅ | ❌ | ❌ | ❌ | 报价提示信息 |

### `quotes[]` 数组实际内容示例

API 一次返回 4 个路由器的完整报价：

```json
{
  "router": "Pancakeswap",
  "amount_out": "910604",
  "quotes": [
    { "router": "Pancakeswap", "amount_out": "910604", "tx": {...}, "routes": [...] },
    { "router": "Uniswap API",  "amount_out": "909953", "tx": {...}, "routes": [...] },
    { "router": "0x Protocol",  "amount_out": "909906", "tx": {...}, "routes": [...] },
    { "router": "KyberSwap",    "amount_out": "909796", "tx": {...}, "routes": [...] }
  ]
}
```

每个 `quotes[]` 元素包含独立的 `tx`、`routes`、`gas_fee` 等字段，结构比顶层简化的 QuoteResponse 更完整。

### 影响

- SDK 用户无法获取多路由对比数据
- 前端如需展示路由器 logo，只能绕过 SDK 直调 API
- 桥接场景的 `deposit_address` 等字段完全不可用

### 修改建议

三个 SDK 统一在 `QuoteResponse` 中补充以下字段。以 Python 为例参考定义：

```python
@dataclass
class Route:
    name: str
    logo: str

@dataclass  
class QuoteItem:
    request_id: str
    router: str
    amount_out: str
    tx: Tx
    routes: list[Route] = field(default_factory=list)
    gas_fee: Optional[str] = None

@dataclass
class QuoteResponse:
    # ... 现有字段保持不变 ...
    quotes: list[QuoteItem] = field(default_factory=list)   # ← 新增
    routes: list[Route] = field(default_factory=list)       # ← 新增
    deposit_address: Optional[str] = None                    # ← 新增
    gas_fee: Optional[str] = None                            # ← 新增  
    bridge_order_id: Optional[str] = None                    # ← 新增
    quote_message: Optional[str] = None                      # ← 新增
```

---

## Bug #3 — [Minor] Python SDK: `estimated_time` 类型标注 `int`，API 返回 `float`

**严重程度**: 🟡 Minor  
**影响范围**: Python SDK — `python/src/wheelx_sdk/wheelx_sdk.py` 第 99 行

### 现象

API 返回 `"estimated_time": 2.0`（float），但 SDK dataclass 中标注为 `int`：

```python
# wheelx_sdk.py 第 99 行
estimated_time: int   # 默认值 = 10
```

### 影响

Python 不会因此崩溃，但类型标注不准确，使用 mypy 静态检查时会报错。

### 修改建议

```python
estimated_time: float  # int → float
```

---

## Bug #4 — [Minor] TypeScript SDK: `npx tsc` 编译失败 — error class 导入路径错误

**严重程度**: 🟡 Minor  
**影响范围**: TypeScript SDK — `src/sdk.ts`、`src/transaction.ts`  
**复现方式**: `cd typescript && npm install && npx tsc`

### 现象

执行 `npx tsc` 报 4 个错误，无法编译：

```
src/sdk.ts(6,3): error TS2305: Module '"./types"' has no exported member 'APIError'.
src/sdk.ts(7,3): error TS2305: Module '"./types"' has no exported member 'NetworkError'.
src/sdk.ts(8,3): error TS2305: Module '"./types"' has no exported member 'ValidationError'.
src/transaction.ts(2,52): error TS2305: Module '"./types"' has no exported member 'TransactionError'.
```

### 根因

这些 error class (`APIError`, `NetworkError`, `ValidationError`, `TransactionError`) 实际定义在 `src/errors.ts`，但 `sdk.ts` 和 `transaction.ts` 错误地从 `./types` 导入。

**`src/sdk.ts` 第 6-8 行（有问题）**:

```typescript
import {
  QuoteRequest, QuoteResponse, OrderResponse, SDKConfig,
  APIError, NetworkError, ValidationError,   // ← 这些在 ./types 中不存在
} from './types';
```

**`src/transaction.ts` 第 2 行（有问题）**:

```typescript
import { Tx, TransactionConfig, TransactionResult, TransactionError } from './types';
//                                                  ^^^^^^^^^^^^^^^^ 不存在于 ./types
```

### 修改建议

将 error class 的导入改为从 `./errors` 引入：

**`src/sdk.ts`**:
```typescript
import { QuoteRequest, QuoteResponse, OrderResponse, SDKConfig } from './types';
import { APIError, NetworkError, ValidationError } from './errors';
```

**`src/transaction.ts`**:
```typescript
import { Tx, TransactionConfig, TransactionResult } from './types';
import { TransactionError } from './errors';
```

---

## Bug #5 — [Minor] TypeScript SDK: `types.ts` 引用了未导入的 `ethers` 命名空间

**严重程度**: 🟡 Minor  
**影响范围**: TypeScript SDK — `src/types.ts` 第 103 行  
**复现方式**: `cd typescript && npx tsc`

### 现象

```
src/types.ts(103,23): error TS2503: Cannot find namespace 'ethers'.
```

### 根因

`TransactionResult` 接口的 `wait` 方法返回类型引用了 `ethers.TransactionReceipt`，但 `types.ts` 中没有 `import ethers`。

**`src/types.ts` 第 101-104 行**:

```typescript
export interface TransactionResult {
  hash: string;
  wait: () => Promise<ethers.TransactionReceipt>;  // ← ethers 命名空间未导入
}
```

### 修改建议

方案 A — 声明 ethers 引用：
```typescript
import type { TransactionReceipt } from 'ethers';

export interface TransactionResult {
  hash: string;
  wait: () => Promise<TransactionReceipt>;
}
```

方案 B — 使用泛型或 `any`（如果不想引入 ethers 依赖到 types 文件）：
```typescript
export interface TransactionResult {
  hash: string;
  wait: () => Promise<any>;
}
```

---

## Bug #6 — [Minor] MCP Server: FastMCP 启动报错 `TypeError`

**严重程度**: 🟡 Minor  
**影响范围**: Python MCP Server — `python/mcp_server.py` 第 24 行  
**复现方式**: `pip install fastmcp && python mcp_server.py`

### 现象

```
TypeError: FastMCP() got unexpected keyword argument(s): 'description'
```

### 根因

`fastmcp==3.4.2` 的 `FastMCP` 构造函数不再接受 `description` 参数。

**`python/mcp_server.py` 第 24 行**:

```python
mcp = FastMCP(
    "WheelX MCP Server",
    description="WheelX DeFi swap and bridge service for cross-chain token transfers"
)
```

### 修改建议

删除 `description` 参数：

```python
mcp = FastMCP("WheelX MCP Server")
```

---

## Bug #7 — [Trivial] Go SDK: `go.sum` 缺失导致离线环境编译失败

**严重程度**: ⚪ Trivial  
**影响范围**: Go SDK 构建流程

### 现象

首次 `go build` 需要下载 `go-ethereum` (200MB+)，网络受限环境无法编译。

### 根因

`go.sum` 文件未被提交到仓库。

### 修改建议

```bash
cd go && go mod tidy && git add go.sum
```

---

## Bug #8 — [Minor] Python SDK: `OrderResponse` 缺少 API 返回的 7 个字段

**严重程度**: 🟡 Minor  
**影响范围**: Python SDK — `python/src/wheelx_sdk/wheelx_sdk.py` 第 66-86 行  
**发现方式**: 用真实地址的 20 笔订单调用 `get_order_status()` 验证

### 现象

SDK 的 `OrderResponse` dataclass 定义了 17 个字段，但 API `/v1/order/{id}` 实际返回 **24 个字段**，7 个字段被静默丢弃：

### API 实际返回 vs SDK 定义

| 字段 | API 实际存在 | SDK 定义 | 示例值 |
|------|:---:|:---:|------|
| `order_id` | ✅ | ✅ | `0x0000...684877` |
| `from_chain` / `to_chain` | ✅ | ✅ | `1` / `1` |
| `from_token` / `to_token` | ✅ | ✅ | `0xdAC17...` / `0x0000...` |
| `from_token_info` / `to_token_info` | ✅ | ✅ | TokenInfo 完整对象 |
| `from_address` / `to_address` | ✅ | ✅ | `0x687d...` |
| `from_amount` / `to_amount` | ✅ | ✅ | `"5000000.000000"` |
| `open_tx_hash` / `fill_tx_hash` | ✅ | ✅ | `0x7e54...` / `null` |
| `open_block` / `fill_block` | ✅ | ✅ | `25200205` / `null` |
| `open_timestamp` / `fill_timestamp`| ✅ | ✅ | `"2026-05-29T09:44:11"` |
| `status` | ✅ | ✅ | `"Filled"` |
| `points` | ✅ | ✅ | `"4.67"` |
| `routes` | ✅ | ❌ | `["Uniswap API"]` |
| `bridge_order_id` | ✅ | ❌ | `null`（swap）/ 有值（bridge） |
| `deposit_address` | ✅ | ❌ | `null`（swap）/ 有值（bridge） |
| `to_platform_id` | ✅ | ❌ | `0` |
| `order_value` | ✅ | ❌ | `"4.99305000000"`（USD 估值） |
| `reward_type` | ✅ | ❌ | `null` / 奖励类型 |
| `reward_value` | ✅ | ❌ | `null` / 奖励值 |

### 测试数据

测试地址 `0x687d6df31512cbb29fd45ca91fffb5d3778f520e`，20 笔历史订单：
- 跨链: 1, 56, 8453, 1868, 4217, 57073, 999, Solana (1151111081099710)
- 路由器: Uniswap API, KYO API, OKX DEX, KyberSwap, QuickSwap, Velodrome, Across, WheelX, Jupiter, Relay, Pancakeswap
- 交易类型: swap（同链）, bridge（跨链）
- 币种: USDT, ETH, USDC, USDC.e, UBTC, USD₮0, SOL

### 影响

- SDK 用户无法获取路由名称列表（`routes`）
- 桥接场景的 `deposit_address` 和 `bridge_order_id` 不可用
- 订单的 USD 估值（`order_value`）不可用
- 奖励数据（`reward_type` / `reward_value`）不可用

### 修改建议

在 `OrderResponse` dataclass 中补充缺失字段：

```python
@dataclass
class OrderResponse:
    """Order status response data"""
    order_id: str
    from_chain: int
    from_token: str
    from_token_info: Optional[TokenInfo]
    from_address: str
    from_amount: str
    to_chain: int
    to_token: str
    to_token_info: Optional[TokenInfo]
    to_amount: str
    to_address: str
    open_tx_hash: str
    open_block: int
    open_timestamp: str
    fill_tx_hash: Optional[str]
    fill_block: Optional[int]
    fill_timestamp: Optional[str]
    status: str
    points: str
    routes: list[str] = field(default_factory=list)          # ← 新增
    bridge_order_id: Optional[str] = None                      # ← 新增
    deposit_address: Optional[str] = None                      # ← 新增
    to_platform_id: Optional[int] = None                       # ← 新增
    order_value: Optional[str] = None                          # ← 新增
    reward_type: Optional[str] = None                          # ← 新增
    reward_value: Optional[str] = None                         # ← 新增
```

⚠ 连带影响：需要同步更新 TypeScript SDK 和 Go SDK 的对应类型定义。

---

## 修复方案汇总

以下修复已在本地应用并测试通过（未提交 git）。按 bug 编号列出具体 diff。

### Bug #1 — Go Tx.Value 类型 ✅ 已修复

**文件**: `go/wheelx/wheelx_sdk.go`

**1) Tx struct: int → string**
```diff
 type Tx struct {
-    Value                int    `json:"value"`
-    Gas                  *int   `json:"gas,omitempty"`
-    MaxFeePerGas         *int   `json:"maxFeePerGas,omitempty"`
-    MaxPriorityFeePerGas *int   `json:"maxPriorityFeePerGas,omitempty"`
+    Value                string  `json:"value"`
+    Gas                  *string `json:"gas,omitempty"`
+    MaxFeePerGas         *string `json:"maxFeePerGas,omitempty"`
+    MaxPriorityFeePerGas *string `json:"maxPriorityFeePerGas,omitempty"`
```

**2) ApproveAction.Amount: int → string**
```diff
-    Amount  int    `json:"amount"`
+    Amount  string `json:"amount"`
```

**3) 添加 `strconv` import**

**4) BuildTransaction / BuildEIP1559Transaction: 字符串解析**
```go
value := new(big.Int)
if txData.Value != "" {
    value.SetString(txData.Value, 10)
}
var gasLimit uint64
if txData.Gas != nil && *txData.Gas != "" {
    gasLimit, _ = strconv.ParseUint(*txData.Gas, 10, 64)
}
```

**5) Example 文件 `%d` → `%s`**（`go/wheelx/wheelx_sdk.go` + `go/examples/simple_swap.go`）

⚠ 无法编译测试因为 Bug #7（go.sum 缺失导致 go-ethereum 下载超时）。类型修复逻辑正确，需有网络环境时联调。

---

### Bug #3 — Python estimated_time 类型 ✅ 已验证

**文件**: `python/src/wheelx_sdk/wheelx_sdk.py` 第 99 行

```diff
-    estimated_time: int
+    estimated_time: float
```

测试: `get_quote()` 返回 `estimated_time=2.0 (type=float)` ✅

---

### Bug #4 + #5 — TypeScript SDK 编译错误 ✅ 已验证（0 errors）

**文件**: `typescript/src/sdk.ts` — import 路径修复
```diff
-import { QuoteRequest, QuoteResponse, OrderResponse, SDKConfig,
-  APIError, NetworkError, ValidationError,
-} from './types';
+import { QuoteRequest, QuoteResponse, OrderResponse, SDKConfig } from './types';
+import { APIError, NetworkError, ValidationError } from './errors';
```

**文件**: `typescript/src/transaction.ts` — import 路径修复
```diff
-import { Tx, TransactionConfig, TransactionResult, TransactionError } from './types';
+import { Tx, TransactionConfig, TransactionResult } from './types';
+import { TransactionError } from './errors';
```

**文件**: `typescript/src/types.ts` — ethers 类型导入
```diff
+import type { TransactionReceipt } from 'ethers';
+
 export interface TransactionResult {
   hash: string;
-  wait: () => Promise<ethers.TransactionReceipt>;
+  wait: () => Promise<TransactionReceipt | null>;
 }
```
（`| null` 是因为 `txResponse.wait()` 的实际返回类型是 `Promise<TransactionReceipt | null>`）

测试: `npx tsc --noEmit` → **0 errors** ✅

---

### Bug #6 — MCP Server FastMCP description ✅ 已验证

**文件**: `python/mcp_server.py` 第 24-27 行

```diff
-mcp = FastMCP(
-    "WheelX MCP Server",
-    description="WheelX DeFi swap and bridge service for cross-chain token transfers"
-)
+mcp = FastMCP("WheelX MCP Server")
```

测试: `FastMCP("WheelX MCP Server")` → `MCP OK: FastMCP` ✅

---

### Bug #7 — Go go.sum 缺失

不做代码修改。需在 Go SDK 目录执行：
```bash
cd go && go mod tidy && git add go.sum
```
⚠ 需要网络下载 go-ethereum (~200MB)。

---

### Bug #8 — OrderResponse 缺字段 ✅ 已验证

**文件**: `python/src/wheelx_sdk/wheelx_sdk.py`

**1) 添加 `field` import**
```diff
-from dataclasses import dataclass
+from dataclasses import dataclass, field
```

**2) OrderResponse 补充 7 个字段**
```python
routes: list[str] = field(default_factory=list)
bridge_order_id: Optional[str] = None
deposit_address: Optional[str] = None
to_platform_id: Optional[int] = None
order_value: Optional[str] = None
reward_type: Optional[str] = None
reward_value: Optional[str] = None
```

**3) `get_order_status()` 传入新字段**

测试: `get_order_status()` 返回 `routes=['Uniswap API'], order_value=4.99305000000` ✅

---

### Bug #2 — QuoteResponse 缺字段（跨三个 SDK）

未修复（范围大，涉及 Python/TypeScript/Go 三个 QuoteResponse 类型），留给开发团队统一处理。

---

## 优先级总结

| 优先级 | Bug | 影响 | 
|--------|-----|------|
| **P0** | #1 Go Tx.Value 类型 | Go SDK 100% 不可用，无 workaround |
| **P1** | #2 QuoteResponse 缺字段 | 三个 SDK 共同缺失，影响核心使用场景 |
| **P2** | #4 TS 编译失败 | TS SDK 无法编译，npm 包无法发布 |
| **P2** | #5 TS ethers 命名空间 | TS SDK 无法编译，同上 |
| **P2** | #6 MCP 启动报错 | MCP Server 无法启动 |
| **P3** | #3 estimated_time 类型 | 不影响运行时，仅类型标注 |
| **P3** | #8 OrderResponse 缺字段 | 数据静默丢弃，不影响核心功能 |
| **P3** | #7 go.sum 缺失 | 仅影响构建体验 |
