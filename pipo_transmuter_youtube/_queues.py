import ssl
import logging

from opentelemetry import metrics, trace
from prometheus_client import REGISTRY
from faststream.rabbit import (
    ExchangeType,
    RabbitExchange,
    RabbitQueue,
)
from faststream.rabbit.fastapi import RabbitRouter, Logger, Context
from faststream.rabbit.prometheus import RabbitPrometheusMiddleware
from faststream.rabbit.opentelemetry import RabbitTelemetryMiddleware
from faststream.security import BaseSecurity

from pipo_transmuter_youtube.telemetry import setup_telemetry
from pipo_transmuter_youtube.config import settings
from pipo_transmuter_youtube.models import ProviderOperation, Music
from pipo_transmuter_youtube.handler import (
    YoutubeHandler,
    YoutubeQueryHandler,
    YoutubeOperations,
)

tracer = trace.get_tracer(__name__)
meter = metrics.get_meter(__name__)


def __load_router(service_name: str) -> RabbitRouter:
    telemetry = setup_telemetry(service_name, settings.telemetry.local)
    core_router = RabbitRouter(
        app_id=settings.app,
        url=settings.queue_broker_url,
        host=settings.player.queue.broker.host,
        virtualhost=settings.player.queue.broker.vhost,
        port=settings.player.queue.broker.port,
        timeout=settings.player.queue.broker.timeout,
        max_consumers=settings.player.queue.broker.max_consumers,
        graceful_timeout=settings.player.queue.broker.graceful_timeout,
        logger=logging.getLogger(__name__),
        security=BaseSecurity(ssl_context=ssl.create_default_context()),
        middlewares=(
            RabbitPrometheusMiddleware(
                registry=REGISTRY,
                app_name=settings.telemetry.metrics.service,
                metrics_prefix="faststream",
            ),
            RabbitTelemetryMiddleware(tracer_provider=telemetry.traces or None),
        ),
    )
    return core_router


router = __load_router(settings.app)


def get_router():
    return router


def get_broker():
    return router.broker


provider_exch = RabbitExchange(
    settings.player.queue.service.transmuter.exchange,
    type=ExchangeType.TOPIC,
    durable=True,
)

youtube_playlist_queue = RabbitQueue(
    settings.player.queue.service.transmuter.youtube_playlist.queue,
    routing_key=settings.player.queue.service.transmuter.youtube_playlist.routing_key,
    durable=True,
    arguments=settings.player.queue.service.transmuter.youtube_playlist.args,
)

youtube_playlist_publisher = router.broker.publisher(
    exchange=provider_exch,
    routing_key=settings.player.queue.service.transmuter.youtube.routing_key,
    description="Produces to provider exchange with key provider.youtube.url",
)

youtube_query_queue = RabbitQueue(
    settings.player.queue.service.transmuter.youtube_query.queue,
    routing_key=settings.player.queue.service.transmuter.youtube_query.routing_key,
    durable=True,
    arguments=settings.player.queue.service.transmuter.youtube_query.args,
)

youtube_queue = RabbitQueue(
    settings.player.queue.service.transmuter.youtube.queue,
    routing_key=settings.player.queue.service.transmuter.youtube.routing_key,
    durable=True,
    arguments=settings.player.queue.service.transmuter.youtube.args,
)


processed_query_success_counter = meter.create_counter(
    name="pipo.transmuter.youtube.query.success",
    description="Number of youtube url queries processed successfully",
    unit="requests",
)


@router.subscriber(
    queue=youtube_query_queue,
    exchange=provider_exch,
    description="Consumes from provider topic with provider.youtube.query key",
)
@router.publisher(
    exchange=provider_exch,
    routing_key=settings.player.queue.service.transmuter.youtube.routing_key,
    description="Produces to provider topic with provider.youtube.url key with increased priority",
    priority=settings.player.queue.service.transmuter.youtube_query.message_priority,
)
async def transmute_youtube_query(
    request: ProviderOperation,
    logger: Logger,
) -> ProviderOperation:
    logger.debug("Received request: %s", request)
    source = await YoutubeQueryHandler.url_from_query(request.query)
    if source:
        request = ProviderOperation(
            uuid=request.uuid,
            server_id=request.server_id,
            provider=settings.player.queue.service.transmuter.youtube.routing_key,
            operation=YoutubeOperations.URL,
            query=source,
        )
        logger.info("Transmuted youtube query: %s", request.uuid)
        processed_query_success_counter.add(1)
        return request


processed_playlist_success_counter = meter.create_counter(
    name="pipo.transmuter.youtube.playlist.success",
    description="Number of youtube playlists processed successfully",
    unit="requests",
)

processed_playlist_songs = meter.create_histogram(
    name="pipo.playlist.songs",
    description="Number of songs contained in processed playlists",
    unit="songs",
)


@router.subscriber(
    queue=youtube_playlist_queue,
    exchange=provider_exch,
    description="Consumes from provider topic with provider.youtube.playlist key",
)
async def transmute_youtube_playlist(
    request: ProviderOperation,
    logger: Logger,
    correlation_id: str = Context("message.correlation_id"),
) -> None:
    logger.debug("Received request: %s", request)
    tracks = YoutubeHandler.parse_playlist(request.query)
    tracks_len = 0
    for url in tracks:
        query = ProviderOperation(
            uuid=request.uuid,
            server_id=request.server_id,
            provider=settings.player.queue.service.transmuter.youtube.routing_key,
            operation=YoutubeOperations.URL,
            query=url,
        )
        tracks_len += 1
        await youtube_playlist_publisher.publish(
            query,
            correlation_id=correlation_id,
        )
    logger.info("Transmuted youtube playlist: %s", request.uuid)
    processed_playlist_success_counter.add(1)
    processed_playlist_songs.record(tracks_len, {"source": "youtube"})


processed_url_success_counter = meter.create_counter(
    name="pipo.transmuter.youtube.url.success",
    description="Number of youtube url processed successfully",
    unit="requests",
)


@router.subscriber(
    queue=youtube_queue,
    exchange=provider_exch,
    description="Consumes from provider topic with provider.youtube.url key and produces to hub exchange",
)
async def transmute_youtube(
    request: ProviderOperation,
    logger: Logger,
    correlation_id: str = Context("message.correlation_id"),
) -> None:
    logger.debug("Received request: %s", request)
    source = YoutubeHandler.get_audio(request.query)
    logger.debug("Obtained youtube audio url: %s", source)
    if source:
        music = Music(
            uuid=request.uuid,
            server_id=request.server_id,
            source=source,
        )
        routing_key = (
            f"{settings.player.queue.service.hub.base_routing_key}.{music.server_id}"
        )
        await router.broker.publish(
            music,
            routing_key=routing_key,
            exchange=settings.player.queue.service.hub.exchange,
            correlation_id=correlation_id,
        )
        processed_url_success_counter.add(1)
        logger.info("Transmuted youtube music: %s", music.uuid)
