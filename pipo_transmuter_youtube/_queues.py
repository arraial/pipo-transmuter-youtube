import ssl
import logging

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
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

from pipo_transmuter_youtube.config import settings
from pipo_transmuter_youtube.models import ProviderOperation, Music
from pipo_transmuter_youtube.handler import (
    YoutubeHandler,
    YoutubeQueryHandler,
    YoutubeOperations,
)

tracer_provider = TracerProvider(
    resource=Resource.create(attributes={"service.name": "faststream"})
)
trace.set_tracer_provider(tracer_provider)

router = RabbitRouter(
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
        RabbitPrometheusMiddleware(registry=REGISTRY),
        RabbitTelemetryMiddleware(tracer_provider=tracer_provider),
    ),
)

broker = router.broker


@router.get("/livez")
async def liveness() -> bool:
    return True


@router.get("/readyz")
async def readiness() -> bool:
    return await router.broker.ping(timeout=settings.probes.readiness.timeout)


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

youtube_playlist_publisher = broker.publisher(
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
        return request


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
    for url in tracks:
        query = ProviderOperation(
            uuid=request.uuid,
            server_id=request.server_id,
            provider=settings.player.queue.service.transmuter.youtube.routing_key,
            operation=YoutubeOperations.URL,
            query=url,
        )
        await youtube_playlist_publisher.publish(
            query,
            correlation_id=correlation_id,
        )
    logger.info("Transmuted youtube playlist: %s", request.uuid)


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
        await broker.publish(
            music,
            routing_key=routing_key,
            exchange=settings.player.queue.service.hub.exchange,
            correlation_id=correlation_id,
        )
        logger.info("Transmuted youtube music: %s", music.uuid)
