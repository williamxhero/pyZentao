import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import asyncio
from zentao_api.core.client import ZentaoClient

async def main():
    client = ZentaoClient(
        base_url="http://192.168.0.72/zentao",
        username="the_account",
        password="the_password"
    )
    try:
        # 调用新版接口，获取token
        token_resp = await client.tokens.postTokens(body={
            "account": "the_account",
            "password": "the_password"
        })
        print("登录成功，Token响应：", token_resp)
    except Exception as e:
        print("登录失败:", e)
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
