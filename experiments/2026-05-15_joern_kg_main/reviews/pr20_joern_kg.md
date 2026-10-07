# Review Note — Evidence-Anchored

**Scope:** This PR re-enables and converts the `SaslApiVersionsRequestTest` to use the new `ClusterTest` framework for KRAFT, removing the legacy `SaslSetup` and custom `ClusterTemplate` configuration.

## Problem

1.  **Incomplete SASL Configuration for KRAFT ClusterTest:** The PR removes the explicit JAAS configuration and SASL mechanism settings previously handled by `SaslSetup` and the `saslApiVersionsRequestClusterConfig` object. While the `@ClusterTest` annotation now specifies `brokerSecurityProtocol = SecurityProtocol.SASL_PLAINTEXT`, this alone does not automatically configure the necessary JAAS context or ensure the `PLAIN` SASL mechanism is enabled and configured for the broker and client within the `ClusterTest` framework. This will lead to SASL authentication failures during test execution.
2.  **Missing SASL Mechanism Configuration:** The previous test explicitly configured `SASL_MECHANISM_INTER_BROKER_PROTOCOL_CONFIG`, `SASL_ENABLED_MECHANISMS_CONFIG`, and `SaslConfigs.SASL_MECHANISM` to use the `PLAIN` mechanism. This specific configuration is now absent. The `sendSaslHandshakeRequestValidateResponse` method still attempts to perform a SASL handshake using the `PLAIN` mechanism, which may not be enabled or correctly configured without these explicit settings, leading to handshake failures.

## Evidence

*   **Problem 1 (Incomplete SASL Configuration):**
    *   `core/src/test/scala/unit/kafka/server/SaslApiVersionsRequestTest.scala:20-21`: Removal of imports for `kafka.api.SaslSetup` and `kafka.security.JaasTestUtils`.
    *   `core/src/test/scala/unit/kafka/server/SaslApiVersionsRequestTest.scala:40-44`: Removal of the `setupSasl()` method, which previously called `sasl.startSasl(sasl.jaasSections(kafkaServerSaslMechanisms, Some(kafkaClientSaslMechanism), JaasTestUtils.KAFKA_SERVER_CONTEXT_NAME))` to configure JAAS.
    *   `core/src/test/scala/unit/kafka/server/SaslApiVersionsRequestTest.scala:115-118`: Removal of the `closeSasl()` method, which handled SASL teardown.
    *   *Structural Context:* The `ClusterTest` annotation in `org.apache.kafka.common.test.api.ClusterTest` and `ClusterTestExtensions` in `org.apache.kafka.common.test.junit.ClusterTestExtensions` primarily configure security protocols and cluster types, but do not expose direct parameters for programmatic JAAS configuration for specific SASL mechanisms.
*   **Problem 2 (Missing SASL Mechanism Configuration):**
    *   `core/src/test/scala/unit/kafka/server/SaslApiVersionsRequestTest.scala:24-37`: Removal of the `saslApiVersionsRequestClusterConfig` object, which previously set `BrokerSecurityConfigs.SASL_MECHANISM_INTER_BROKER_PROTOCOL_CONFIG`, `BrokerSecurityConfigs.SASL_ENABLED_MECHANISMS_CONFIG`, and `SaslConfigs.SASL_MECHANISM` to `PLAIN`.
    *   `core/src/test/scala/unit/kafka/server/SaslApiVersionsRequestTest.scala:110`: The `sendSaslHandshakeRequestValidateResponse` method still constructs a `SaslHandshakeRequest` with `setMechanism("PLAIN")`, assuming the `PLAIN` mechanism is available and configured.

## Impact

The re-enabled tests will likely fail due to SASL authentication errors (e.g., `SaslAuthenticationException`) or handshake failures. This means the PR will not achieve its goal of re-enabling functional SASL API versions tests for KRAFT, leading to a false sense of test coverage for critical security functionality. The behavior of `ApiVersionsRequest` before and after `SaslHandshakeRequest` in a SASL-enabled KRAFT environment will remain untested.

## Recommendation (Fix / Tests / Risks)

1.  **Re-introduce SASL JAAS Configuration:**
    *   Investigate how the `ClusterTest` framework is intended to handle programmatic JAAS configuration for SASL mechanisms.
    *   If `ClusterTest` does not provide this directly, the test must re-introduce the necessary JAAS setup. This could involve:
        *   Extending `ClusterTestExtensions` to inject JAAS configuration.
        *   Using a custom `ClusterInstance` builder that includes JAAS setup.
        *   Re-introducing a `BeforeEach` method that calls a utility function to set up JAAS, similar to the removed `sasl.startSasl` call, ensuring it's compatible with the `ClusterTest` lifecycle.
    *   The goal is to ensure the equivalent of `sasl.startSasl(sasl.jaasSections(kafkaServerSaslMechanisms, Some(kafkaClientSaslMechanism), JaasTestUtils.KAFKA_SERVER_CONTEXT_NAME))` is performed before the broker starts.
2.  **Explicitly Configure SASL Mechanisms:**
    *   Ensure that the `PLAIN` SASL mechanism is explicitly enabled and configured for both the broker and client within the `ClusterTest` setup. This might involve adding specific properties to the `@ClusterTest` annotation if the framework supports it (e.g., `brokerProperties = Array("sasl.enabled.mechanisms=PLAIN")`, `clientProperties = Array("sasl.mechanism=PLAIN")`).
    *   Verify that the `ClusterInstance` created by `ClusterTestExtensions` correctly sets `BrokerSecurityConfigs.SASL_ENABLED_MECHANISMS_CONFIG` and `SaslConfigs.SASL_MECHANISM` to `PLAIN`.
3.  **Verify Test Execution:** After implementing the above, run the `SaslApiVersionsRequestTest` to confirm that the `testApiVersionsRequestBeforeSaslHandshakeRequest()`, `testApiVersionsRequestAfterSaslHandshakeRequest()`, and `testApiVersionsRequestWithUnsupportedVersion()` methods pass without SASL-related errors.

## Traceability
Not specified