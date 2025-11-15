import os
import sys
import base64
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fetch_subscriptions import parse_proxy_url, fetch_subscription


class MockResponse:
    def __init__(self, text, content_type='text/plain'):
        self.text = text
        self.headers = {'Content-Type': content_type}
        self.status_code = 200

    def raise_for_status(self):
        pass


class TestParseProxyUrl(unittest.TestCase):
    def test_parse_tuic_url(self):
        url = (
            'tuic://uuid:password@example.com:10443?'
            'alpn=h3,h3-29&congestion_control=bbr&peer=example.com&'
            'udp_relay_mode=native&insecure=1#MyTUIC'
        )
        node = parse_proxy_url(url)
        self.assertIsNotNone(node)
        self.assertEqual('tuic', node.get('type'))
        self.assertEqual('example.com', node.get('server'))
        self.assertEqual(10443, node.get('port'))
        self.assertEqual('uuid', node.get('uuid'))
        self.assertEqual('password', node.get('password'))
        self.assertEqual(['h3', 'h3-29'], node.get('alpn'))
        self.assertEqual('bbr', node.get('congestion-control'))
        self.assertEqual('example.com', node.get('sni'))
        self.assertEqual('native', node.get('udp-relay-mode'))
        self.assertTrue(node.get('skip-cert-verify'))

    def test_parse_wireguard_url(self):
        url = (
            'wireguard://clientPrivateKey@example.com:51820?'
            'public-key=serverPub&ip=10.0.0.2/32&dns=1.1.1.1,8.8.8.8&'
            'keepalive=25&preSharedKey=preshared#WG'
        )
        node = parse_proxy_url(url)
        self.assertIsNotNone(node)
        self.assertEqual('wireguard', node.get('type'))
        self.assertEqual('example.com', node.get('server'))
        self.assertEqual(51820, node.get('port'))
        self.assertEqual('clientPrivateKey', node.get('private-key'))
        self.assertEqual('serverPub', node.get('public-key'))
        self.assertEqual('preshared', node.get('pre-shared-key'))
        self.assertEqual('10.0.0.2/32', node.get('ip'))
        self.assertEqual(['1.1.1.1', '8.8.8.8'], node.get('dns'))
        self.assertEqual(25, node.get('keepalive'))

    def test_parse_https_proxy(self):
        url = 'https://user:pass@example.com:8443?skip-cert-verify=1#MyHTTP'
        node = parse_proxy_url(url)
        self.assertIsNotNone(node)
        self.assertEqual('http', node.get('type'))
        self.assertEqual('example.com', node.get('server'))
        self.assertEqual(8443, node.get('port'))
        self.assertEqual('user', node.get('username'))
        self.assertEqual('pass', node.get('password'))
        self.assertTrue(node.get('tls'))
        self.assertTrue(node.get('skip-cert-verify'))

    def test_parse_socks_proxy(self):
        url = 'socks://user:pass@example.com:1080?udp=1#SockProxy'
        node = parse_proxy_url(url)
        self.assertIsNotNone(node)
        self.assertEqual('socks5', node.get('type'))
        self.assertEqual('example.com', node.get('server'))
        self.assertEqual(1080, node.get('port'))
        self.assertEqual('user', node.get('username'))
        self.assertEqual('pass', node.get('password'))
        self.assertTrue(node.get('udp'))


class TestFetchSubscription(unittest.TestCase):
    def test_fetch_subscription_parses_new_protocols_in_base64(self):
        tuic_url = (
            'tuic://uuid:password@example.com:10443?'
            'alpn=h3,h3-29&congestion_control=bbr&peer=example.com&'
            'udp_relay_mode=native#MyTUIC'
        )
        https_url = 'https://user:pass@example.com:8080#HttpProxy'
        content = base64.b64encode(f"{tuic_url}\n{https_url}".encode('utf-8')).decode('utf-8')

        response = MockResponse(content)
        with patch('fetch_subscriptions.requests.get', return_value=response) as mock_get, \
                patch('fetch_subscriptions.cloudscraper.create_scraper') as mock_scraper:
            mock_scraper.side_effect = AssertionError('cloudscraper should not be used when requests succeeds')
            nodes = fetch_subscription('https://example.com/subscription')

        mock_get.assert_called_once()
        self.assertIsNotNone(nodes)
        self.assertEqual(2, len(nodes))
        self.assertEqual('tuic', nodes[0].get('type'))
        self.assertEqual('http', nodes[1].get('type'))

    def test_fetch_subscription_parses_new_protocols_in_plain_text(self):
        wireguard_url = 'wireguard://clientKey@example.com:51820?public-key=serverKey#WireGuardProxy'
        socks_url = 'socks://user:pass@example.com:1080?udp=1#SockProxy'
        content = f"{wireguard_url}\n{socks_url}"

        response = MockResponse(content)
        with patch('fetch_subscriptions.requests.get', return_value=response) as mock_get, \
                patch('fetch_subscriptions.cloudscraper.create_scraper') as mock_scraper:
            mock_scraper.side_effect = AssertionError('cloudscraper should not be used when requests succeeds')
            nodes = fetch_subscription('https://example.com/subscription')

        mock_get.assert_called_once()
        self.assertIsNotNone(nodes)
        self.assertEqual(2, len(nodes))
        types = {node.get('type') for node in nodes}
        self.assertIn('wireguard', types)
        self.assertIn('socks5', types)


if __name__ == '__main__':
    unittest.main()
