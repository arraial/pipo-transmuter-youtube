import pytest
import tests.constants
from tests.conftest import Helpers
from faststream.rabbit import TestRabbitBroker, RabbitQueue
from pipo_transmuter_youtube.handler import YoutubeOperations
from pipo_transmuter_youtube.models import ProviderOperation
from pipo_transmuter_youtube.config import settings
from pipo_transmuter_youtube._queues import (
    router,
    broker,
    transmute_youtube,
    provider_exch,
)

test_queue = RabbitQueue(
    "test-queue",
    routing_key="provider.#",
    auto_delete=True,
)


@router.subscriber(
    queue=test_queue,
    exchange=provider_exch,
    description="Consumes from dispatch topic and produces to provider exchange",
)
async def consume_dummy(
    request: ProviderOperation,
) -> None:
    pass


@pytest.mark.spotify
@pytest.mark.remote_queue
class TestTransmuteUrl:
    @pytest.mark.parametrize(
        "query",
        [
            tests.constants.YOUTUBE_URL_1,
        ],
    )
    @pytest.mark.asyncio
    async def test_transmute_url(self, query):
        server_id = "0"
        uuid = Helpers.generate_uuid()

        async with TestRabbitBroker(
            broker, with_real=settings.player.queue.remote
        ) as br:
            operation_request = ProviderOperation(
                uuid=uuid,
                server_id=server_id,
                provider="provider.youtube.url",
                operation=YoutubeOperations.URL,
                query=query,
            )

            await br.publish(
                operation_request,
                exchange=provider_exch,
                routing_key=operation_request.provider,
            )
            await transmute_youtube.wait_call(timeout=tests.constants.SHORT_TIMEOUT)
            transmute_youtube.mock.assert_called_once_with(dict(operation_request))
            await consume_dummy.wait_call(timeout=tests.constants.MEDIUM_TIMEOUT)
            consume_dummy.mock.assert_called_once()
