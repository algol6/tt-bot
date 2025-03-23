import asyncio
import os
import time

import aiohttp
import bot.api.model as model

sem = asyncio.Semaphore(1)

class SMMOApi:
    _API_URL: str = "https://api.simple-mmo.com/"
    _API_TOKEN: str = os.getenv("SMMO_TOKEN")
    rate_limit_remaining: int = 0
    _first_request_time: float = 0.0
    @staticmethod
    async def _request(endpoint: str) -> dict | list | None:
        async with sem:
            if SMMOApi.rate_limit_remaining <= 0 and SMMOApi._first_request_time > 0.0:
                await asyncio.sleep(60)
                SMMOApi._first_request_time = 0.0

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url=f"{SMMOApi._API_URL}{endpoint.lstrip('/')}",
                    data={
                        "api_key": SMMOApi._API_TOKEN
                    }
                ) as resp:
                    if not resp.ok:
                        print(await resp.text())
                        return None
                    if "X-RateLimit-Remaining" in resp.headers:
                        SMMOApi.rate_limit_remaining = int(resp.headers.get("X-RateLimit-Remaining"))
                        if SMMOApi._first_request_time == 0.0:
                            SMMOApi._first_request_time = time.time()

                    return SMMOApi._fix_names(await resp.json())

    @staticmethod
    def _fix_names(obj: dict | list) -> dict | list | None:
        name_replacements = {
            "def": "defence",
            "str": "strength",
            "dex": "dexterity",
            "type": "item_type"
        }

        if type(obj) is dict:
            if "error" in obj:
                return None
            result: dict = {}

            for k, v in obj.items():
                result[k] = v

                if type(v) is dict:
                    v = SMMOApi._fix_names(obj[k])
                    result[k] = v

                if k in name_replacements:
                    new_key = name_replacements[k]
                    result[new_key] = v
                    del result[k]

            if 'motto' in result and not 'guild' in result:
                result["guild"] = {"id":None,"name":None}

            return result
        else:
            result: list = []

            for v in obj:
                if type(v) is dict:
                    v = SMMOApi._fix_names(v)
                    result.append(v)

            return result

    @staticmethod
    async def get_player_info(player_id: str) -> model.PlayerInfo | None:
        resp = await SMMOApi._request(f"v1/player/info/{player_id}")
        if resp is not None:
            return model.PlayerInfo(**resp)

        return None

    @staticmethod
    async def get_guild_info(guild_id: int) -> model.GuildInfo | None:
        resp = await SMMOApi._request(f"v1/guilds/info/{guild_id}")
        if resp is not None:
            return model.GuildInfo(**resp)

        return None

    @staticmethod
    async def get_guild_members(guild_id: int) -> list[model.GuildMemberInfo]:
        resp = await SMMOApi._request(f"v1/guilds/members/{guild_id}")
        if resp is not None and type(resp) is list:
            return [model.GuildMemberInfo(**v) for v in resp]

        return []