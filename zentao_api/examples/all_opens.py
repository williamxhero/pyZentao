import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
# print cwd:
print(os.getcwd())

import asyncio
from zentao_api.core.client import ZentaoClient

async def main():
    # 初始化 ZentaoClient
    client = ZentaoClient(
        base_url="http://192.168.0.72/zentao/",
        username="the_account",
        password="the_password"
    )

    try:
        # 调用 tokens API 进行登录
        response = await client.tokens.tokens(
            account="the_account",
            password="the_password"
        )
        # 打印登录返回的 token 信息
        print("登录成功，返回信息：")
        print(response)
    except Exception as e:
        print(f"登录失败: {e}")
    finally:
        # 关闭 HTTP 会话
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
