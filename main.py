import aiohttp
import discord
from discord.ext import commands
from discord.gateway import DiscordWebSocket, _log
import asyncio
import logging
import sys
import typing as t

_intents = discord.Intents.all()
_intents.members = True
_intents.presences = True
_intents.message_content = True

logger = logging.getLogger(__name__)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


class MyGateway(DiscordWebSocket):

    async def identify(self):
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'token': self.token,
                'properties': {
                    '$os': sys.platform,
                    '$browser': 'Discord Android',
                    '$device': 'Discord Android',
                    '$referrer': '',
                    '$referring_domain': ''
                },
                'compress': True,
                'large_threshold': 250,
                'v': 3
            }
        }

        if self.shard_id is not None and self.shard_count is not None:
            payload['d']['shard'] = [self.shard_id, self.shard_count]

        state = self._connection
        if state._activity is not None or state._status is not None:
            payload['d']['presence'] = {
                'status': state._status,
                'game': state._activity,
                'since': 0,
                'afk': False
            }

        if state._intents is not None:
            payload['d']['intents'] = state._intents.value

        await self.call_hooks('before_identify', self.shard_id, initial=self._initial_identify)
        await self.send_as_json(payload)
        _log.info('Shard ID %s has sent the IDENTIFY payload.', self.shard_id)


class MyBot(commands.Bot):
    def __init__(self, prefix: t.Optional[str]):
        prefix = prefix or "!"
        super().__init__(prefix, help_command=None, intents=_intents)

    async def connect(self, *, reconnect: bool = True) -> None:
        backoff = discord.client.ExponentialBackoff()
        ws_params = {
            'initial': True,
            'shard_id': self.shard_id,
        }
        while not self.is_closed():
            try:
                coro = MyGateway.from_client(self, **ws_params)
                self.ws = await asyncio.wait_for(coro, timeout=60.0)
                ws_params['initial'] = False
                while True:
                    await self.ws.poll_event()
            except discord.client.ReconnectWebSocket as e:
                _log.info('Got a request to %s the websocket.', e.op)
                self.dispatch('disconnect')
                ws_params.update(sequence=self.ws.sequence, resume=e.resume, session=self.ws.session_id)
                continue
            except (OSError,
                    discord.HTTPException,
                    discord.GatewayNotFound,
                    discord.ConnectionClosed,
                    aiohttp.ClientError,
                    asyncio.TimeoutError) as exc:

                self.dispatch('disconnect')
                if not reconnect:
                    await self.close()
                    if isinstance(exc, discord.ConnectionClosed) and exc.code == 1000:
                        return
                    raise

                if self.is_closed():
                    return

                if isinstance(exc, OSError) and exc.errno in (54, 10054):
                    ws_params.update(sequence=self.ws.sequence, initial=False, resume=True, session=self.ws.session_id)
                    continue

                if isinstance(exc, discord.ConnectionClosed):
                    if exc.code == 4014:
                        raise discord.PrivilegedIntentsRequired(exc.shard_id) from None
                    if exc.code != 1000:
                        await self.close()
                        raise

                retry = backoff.delay()
                _log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry)
                ws_params.update(sequence=self.ws.sequence, resume=True, session=self.ws.session_id)
