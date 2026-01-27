"""
WebSocket routing for VirtuTune

スマホとPCのリアルタイム通信のためのWebSocketルーティング
"""

from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r"ws/guitar/(?P<session_id>[^/]+)/$", consumers.GuitarConsumer.as_asgi()),
]
