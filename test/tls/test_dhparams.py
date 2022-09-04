# -*- coding: utf-8 -*-

try:
    from unittest import mock
except ImportError:
    import mock

from cryptoparser.tls.extension import TlsExtensionsBase, TlsNamedCurve
from cryptoparser.tls.version import TlsVersion, TlsProtocolVersionFinal

from cryptolyzer.common.dhparam import (
    DHPublicKey,
    DHPublicNumbers,
    WellKnownDHParams,
)

from cryptolyzer.tls.client import L7ClientTlsBase, TlsHandshakeClientHelloKeyExchangeDHE
from cryptolyzer.tls.dhparams import AnalyzerDHParams

from .classes import TestTlsCases, L7ServerTlsTest, L7ServerTlsPlainTextResponse


class TestTlsDHParams(TestTlsCases.TestTlsBase):
    @staticmethod
    def get_result(host, port, protocol_version=TlsProtocolVersionFinal(TlsVersion.TLS1_2), timeout=None, ip=None):
        analyzer = AnalyzerDHParams()
        l7_client = L7ClientTlsBase.from_scheme('tls', host, port, timeout, ip)
        result = analyzer.analyze(l7_client, protocol_version)
        return result

    @mock.patch.object(TlsExtensionsBase, 'get_item_by_type', side_effect=KeyError)
    def test_error_missing_key_share_extension(self, _):
        result = self.get_result('mega.co.nz', 443, TlsProtocolVersionFinal(TlsVersion.TLS1_3))
        self.assertEqual(result.groups, [])
        self.assertEqual(result.dhparam, None)

    @mock.patch.object(AnalyzerDHParams, '_get_public_key', side_effect=StopIteration)
    def test_error_no_respoinse_during_key_reuse_check(self, _):
        result = self.get_result('mega.co.nz', 443, TlsProtocolVersionFinal(TlsVersion.TLS1_3))
        self.assertEqual(result.key_reuse, None)

    @mock.patch.object(
        TlsHandshakeClientHelloKeyExchangeDHE, '_NAMED_CURVES',
        mock.PropertyMock(return_value=[TlsNamedCurve.FFDHE2048, ])
    )
    def test_last_key_share_extension(self):
        result = self.get_result('mega.co.nz', 443, TlsProtocolVersionFinal(TlsVersion.TLS1_2))
        self.assertEqual(result.groups, [TlsNamedCurve.FFDHE2048])
        self.assertEqual(result.dhparam, None)

        result = self.get_result('mega.co.nz', 443, TlsProtocolVersionFinal(TlsVersion.TLS1_3))
        self.assertEqual(result.groups, [TlsNamedCurve.FFDHE2048])
        self.assertEqual(result.dhparam, None)

    def test_size(self):
        result = self.get_result('dh480.badssl.com', 443)
        self.assertEqual(result.groups, [])
        self.assertEqual(result.dhparam.key_size, 480)
        self.assertEqual(result.dhparam.prime, True)
        self.assertEqual(result.dhparam.safe_prime, True)
        self.assertEqual(result.dhparam.well_known, None)
        self.assertFalse(result.key_reuse)

    def test_prime(self):
        result = self.get_result('dh-composite.badssl.com', 443)
        self.assertEqual(result.groups, [])
        self.assertEqual(result.dhparam.key_size, 2048)
        self.assertEqual(result.dhparam.prime, False)
        self.assertEqual(result.dhparam.safe_prime, False)
        self.assertEqual(result.dhparam.well_known, None)
        self.assertFalse(result.key_reuse)

    def test_safe_prime(self):
        result = self.get_result('dh-small-subgroup.badssl.com', 443)
        self.assertEqual(result.groups, [])
        self.assertEqual(result.dhparam.key_size, 2048)
        self.assertEqual(result.dhparam.prime, True)
        self.assertEqual(result.dhparam.safe_prime, False)
        self.assertEqual(result.dhparam.well_known, None)
        self.assertFalse(result.key_reuse)

    def test_well_known_prime(self):
        result = self.get_result('ubuntuforums.org', 443)
        self.assertEqual(result.groups, [])
        self.assertEqual(result.dhparam.key_size, 2048)
        self.assertEqual(result.dhparam.prime, True)
        self.assertEqual(result.dhparam.safe_prime, True)
        self.assertEqual(result.dhparam.well_known, WellKnownDHParams.RFC3526_2048_BIT_MODP_GROUP)
        self.assertFalse(result.key_reuse)

    def test_plain_text_response(self):
        threaded_server = L7ServerTlsTest(
            L7ServerTlsPlainTextResponse('localhost', 0, timeout=0.2),
        )
        threaded_server.start()

        result = self.get_result('localhost', threaded_server.l7_server.l4_transfer.bind_port)
        self.assertEqual(result.groups, [])
        self.assertEqual(result.dhparam, None)

    def test_no_dhe_support(self):
        result = self.get_result('static-rsa.badssl.com', 443)
        self.assertEqual(result.groups, [])
        self.assertEqual(result.dhparam, None)
        self.assertEqual(result.key_reuse, None)

    def test_tls_early_version(self):
        result = self.get_result('dh480.badssl.com', 443, TlsProtocolVersionFinal(TlsVersion.TLS1_0))
        self.assertEqual(result.groups, [])
        self.assertNotEqual(result.dhparam, None)
        self.assertFalse(result.key_reuse)

    def test_tls_1_2_rfc_7919_support(self):
        result = self.get_result('mega.co.nz', 443, TlsProtocolVersionFinal(TlsVersion.TLS1_2))
        self.assertEqual(result.groups, [TlsNamedCurve.FFDHE2048])
        self.assertEqual(result.dhparam, None)
        self.assertFalse(result.key_reuse)

    @mock.patch.object(
        AnalyzerDHParams, '_get_public_key_tls_1_x',
        return_value=DHPublicKey(
            DHPublicNumbers(
                0, WellKnownDHParams.RFC7919_4096_BIT_FINITE_FIELD_DIFFIE_HELLMAN_GROUP.value.dh_param_numbers
            ),
            4096
        )
    )
    def test_tls_1_2_no_rfc_7919_support(self, _):
        result = self.get_result('mega.co.nz', 443, TlsProtocolVersionFinal(TlsVersion.TLS1_2))
        self.assertEqual(result.groups, [])
        self.assertEqual(
            result.dhparam.parameter_numbers,
            WellKnownDHParams.RFC7919_4096_BIT_FINITE_FIELD_DIFFIE_HELLMAN_GROUP.value.dh_param_numbers,
        )
        self.assertTrue(result.key_reuse)

    def test_tls_1_3(self):
        result = self.get_result('www.cloudflare.com', 443, TlsProtocolVersionFinal(TlsVersion.TLS1_3))
        self.assertEqual(result.groups, [])
        self.assertEqual(result.dhparam, None)
        self.assertFalse(result.key_reuse)

        result = self.get_result('mega.co.nz', 443, TlsProtocolVersionFinal(TlsVersion.TLS1_3))
        self.assertEqual(result.groups, [TlsNamedCurve.FFDHE2048])
        self.assertEqual(result.dhparam, None)
        self.assertFalse(result.key_reuse)

    def test_json(self):
        result = self.get_result('dh480.badssl.com', 443)
        self.assertTrue(result)
        result = self.get_result('www.owasp.org', 443)
        self.assertTrue(result)
