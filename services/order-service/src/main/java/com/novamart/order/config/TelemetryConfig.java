package com.novamart.order.config;

import io.opentelemetry.api.GlobalOpenTelemetry;
import io.opentelemetry.api.OpenTelemetry;
import io.opentelemetry.api.trace.Tracer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

/**
 * Configuration for OpenTelemetry instrumentation.
 * The EDOT Java agent handles automatic instrumentation, but we provide
 * access to the Tracer API for custom spans (like the bug span).
 * Workshop: From Commit to Culprit - Order Service
 */
@Configuration
public class TelemetryConfig {

    /**
     * Provides the OpenTelemetry Tracer for manual instrumentation.
     * The EDOT Java agent automatically sets up the global OpenTelemetry instance.
     *
     * @return The tracer instance
     */
    @Bean
    public Tracer tracer() {
        OpenTelemetry openTelemetry = GlobalOpenTelemetry.get();
        return openTelemetry.getTracer("order-service", "1.0.0");
    }

    /**
     * Provides a RestTemplate bean for HTTP client calls.
     * The EDOT Java agent automatically instruments this for distributed tracing.
     *
     * @return The RestTemplate instance
     */
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
