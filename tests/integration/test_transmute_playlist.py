import pytest
import mock
from faststream.rabbit import TestRabbitBroker
from pipo_transmuter_youtube.handler import YoutubeOperations
from pipo_transmuter_youtube.models import ProviderOperation
import tests.constants
from tests.conftest import Helpers

from pipo_transmuter_youtube.config import settings

from pipo_transmuter_youtube._queues import (
    broker,
    transmute_youtube,
    transmute_youtube_playlist,
    provider_exch,
)


@pytest.mark.spotify
@pytest.mark.remote_queue
class TestTransmutePlaylist:
    @pytest.mark.parametrize(
        "query, expected",
        [
            (
                tests.constants.YOUTUBE_PLAYLIST_1,
                (tests.constants.YOUTUBE_PLAYLIST_CONTENT_1,),
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_transmute_playlist(self, query, expected):
        server_id = "0"
        uuid = Helpers.generate_uuid()

        async with TestRabbitBroker(
            broker, with_real=settings.player.queue.remote
        ) as br:
            operation_request = ProviderOperation(
                uuid=uuid,
                server_id=server_id,
                provider="provider.youtube.playlist",
                operation=YoutubeOperations.PLAYLIST,
                query=query,
            )

            provider_operations = [
                mock.call(
                    dict(
                        ProviderOperation(
                            uuid=uuid,
                            server_id=server_id,
                            query=content,
                            provider="provider.youtube.url",
                            operation=YoutubeOperations.URL,
                        )
                    )
                )
                for content in expected
            ]

            await br.publish(
                operation_request,
                exchange=provider_exch,
                routing_key=operation_request.provider,
            )
            await transmute_youtube_playlist.wait_call(
                timeout=tests.constants.SHORT_TIMEOUT
            )
            transmute_youtube_playlist.mock.assert_called_once_with(
                dict(operation_request)
            )
            await transmute_youtube.wait_call(timeout=tests.constants.MEDIUM_TIMEOUT)
            transmute_youtube.mock.assert_has_calls(provider_operations, any_order=True)
