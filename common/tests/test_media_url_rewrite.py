"""Unit tests for public MinIO URL rewriting."""

from django.test import SimpleTestCase, override_settings

from common.media_url_rewrite import (
    rewrite_media_urls_in_data,
    rewrite_public_media_url,
)


@override_settings(
    AWS_S3_CUSTOM_DOMAIN="172.16.3.24:8206/minio/zingsa-collect-media",
    AWS_S3_URL_PROTOCOL="http:",
    PUBLIC_MEDIA_RELATIVE=True,
)
class MediaUrlRewriteTests(SimpleTestCase):
    def test_rewrites_direct_minio_port_to_relative(self):
        old = (
            "http://172.30.5.24:9018/zingsa-collect-media/"
            "uploads/%25Y/%25m/photo.jpeg"
        )
        new = rewrite_public_media_url(old)
        self.assertEqual(
            new,
            "/minio/zingsa-collect-media/uploads/%25Y/%25m/photo.jpeg",
        )

    def test_rewrites_external_and_lan_hosts(self):
        for host in ("172.16.3.24:8206", "41.174.184.62:8206"):
            old = f"http://{host}/minio/zingsa-collect-media/a.jpeg"
            self.assertEqual(
                rewrite_public_media_url(old),
                "/minio/zingsa-collect-media/a.jpeg",
            )

    def test_rewrites_nested_payload(self):
        payload = {
            "photos": [
                {
                    "url": "http://172.16.3.24:9018/zingsa-collect-media/a.jpeg",
                    "uri": "http://172.30.5.24:9018/zingsa-collect-media/b.jpeg",
                }
            ]
        }
        out = rewrite_media_urls_in_data(payload)
        self.assertEqual(out["photos"][0]["url"], "/minio/zingsa-collect-media/a.jpeg")
        self.assertEqual(out["photos"][0]["uri"], "/minio/zingsa-collect-media/b.jpeg")

    def test_leaves_unrelated_urls(self):
        url = "http://172.30.5.24:8206/feedback"
        self.assertEqual(rewrite_public_media_url(url), url)
