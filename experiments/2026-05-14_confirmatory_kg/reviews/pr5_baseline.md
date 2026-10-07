# Review Note — Evidence-Anchored

**Scope:** This PR fixes a NullPointerException that occurs when Kafka Connect is started with listener-prefixed SSL configurations, specifically when `ssl.cipher.suites` is not explicitly defined.

## Problem
1.  **NullPointerException:** The original code directly called `.isEmpty()` on the result of `sslConfigValues.get(SslConfigs.SSL_CIPHER_SUITES_CONFIG)`. If `sslConfigValues` did not contain an entry for `SslConfigs.SSL_CIPHER_SUITES_CONFIG` (which can happen with listener-prefixed configurations where non-prefixed counterparts are absent), `get()` would return `null`, leading to a `NullPointerException`.
2.  **Incomplete Null Check:** The previous check `!sslCipherSuites.isEmpty()` assumed `sslCipherSuites` would always be a non-null `List`, even if empty. This assumption was incorrect under specific configuration scenarios.

## Evidence
*   `connect/runtime/src/main/java/org/apache/kafka/connect/runtime/rest/util/SSLUtils.java:137` (Original line: `if (!sslCipherSuites.isEmpty())`)

## Impact
The Kafka Connect REST server would fail to start with a `NullPointerException` if listener-prefixed SSL configurations were used without explicitly providing a value for `ssl.cipher.suites`. This would prevent Connect workers from initializing and serving REST requests, leading to service unavailability.

## Recommendation (Fix / Tests / Risks)
1.  **Fix:** The change `if (sslCipherSuites != null && !sslCipherSuites.isEmpty())` correctly addresses the `NullPointerException` by first checking if `sslCipherSuites` is null before attempting to call `isEmpty()`. This is a robust and appropriate fix.
2.  **Tests:** The added unit tests `testCreateServerSideSslContextFactoryWithListenerPrefixedConfigs` and `testCreateClientSideSslContextFactoryWithListenerPrefixedConfigs` are excellent. They specifically target the problematic scenario of using listener-prefixed configs without all non-prefixed counterparts, ensuring the fix works as intended and preventing future regressions.
3.  **Risks:** The change is minimal and highly targeted. There are no apparent risks introduced by this fix; it only improves the robustness of configuration parsing.

## Traceability
Chia-Ping Tsai