package com.novamart.order;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

/**
 * Main application class for the Order Service.
 * Displays a startup banner with environment and version information.
 * Workshop: From Commit to Culprit - Order Service
 */
@SpringBootApplication
public class OrderServiceApplication {

    private static final Logger log = LoggerFactory.getLogger(OrderServiceApplication.class);

    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }

    /**
     * Displays startup banner showing environment, version, and Elastic connection status.
     * This helps workshop participants understand which version is running.
     */
    @Bean
    public CommandLineRunner startupBanner(
            @Value("${spring.application.name}") String serviceName,
            @Value("${server.port}") int port,
            @Value("${order.service.version:v1.0}") String version,
            @Value("${order.service.environment:local}") String environment,
            @Value("${order.service.bug.enabled:false}") boolean bugEnabled,
            @Value("${services.inventory.url}") String inventoryUrl,
            @Value("${services.payment.url}") String paymentUrl) {

        return args -> {
            String banner = """

                    ============================================================
                    NovaMart Order Service - From Commit to Culprit Workshop
                    ============================================================
                    Service:      %s
                    Version:      %s %s
                    Environment:  %s
                    Port:         %d
                    ------------------------------------------------------------
                    Dependencies:
                      - Inventory Service: %s
                      - Payment Service:   %s
                    ------------------------------------------------------------
                    Telemetry:
                      - EDOT Java Agent:   Enabled
                      - Trace Propagation: W3C Trace Context
                      - Log Correlation:   trace_id in MDC
                    ============================================================

                    """.formatted(
                    serviceName,
                    version,
                    bugEnabled ? "(BUG ENABLED)" : "",
                    environment,
                    port,
                    inventoryUrl,
                    paymentUrl
            );

            System.out.println(banner);

            if (bugEnabled) {
                log.warn("============================================================");
                log.warn("WORKSHOP WARNING: Running v1.1-bad with performance bug!");
                log.warn("This version includes Jordan Rivera's trace logging optimization");
                log.warn("that adds a 2-second delay to every order creation.");
                log.warn("Participants will discover this issue using Elastic Observability.");
                log.warn("============================================================");
            } else {
                log.info("Running healthy baseline version v1.0");
            }

            log.info("Order Service started successfully on port {}", port);
            log.info("Health check available at: http://localhost:{}/api/orders/health", port);
            log.info("Ready check available at: http://localhost:{}/api/orders/ready", port);
        };
    }
}
