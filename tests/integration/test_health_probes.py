#!usr/bin/env python3
import pytest
from fastapi.testclient import TestClient
from faststream.rabbit import TestRabbitBroker

from pipo_transmuter_youtube.app import create_app
from pipo_transmuter_youtube.config import settings
from pipo_transmuter_youtube._queues import get_broker, get_router


@pytest.mark.integration
class TestHealthProbes:
    @pytest.fixture
    async def client(self):
        async with TestRabbitBroker(get_broker()):
            yield TestClient(create_app(get_router()))

    def test_livez(self, client):
        response = client.get("/livez", timeout=settings.probes.liveness.timeout)
        assert response.status_code == settings.probes.liveness.status_code

    def test_readyz(self, client):
        response = client.get("/readyz", timeout=settings.probes.readiness.timeout)
        assert response.status_code == 204
